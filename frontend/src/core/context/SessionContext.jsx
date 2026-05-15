import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
} from 'react';
import { isWeakLabel, mergeSessionLabels } from './sessionMerge';
import { API_BASE } from '../config/apiBase';

const SessionContext = createContext();
const SWITCH_TIMEOUT_MS = 130_000;

/** LAB | PRODUCTION — normaliza .env (espaços, casing) */
const resolveInitialAppMode = () => {
  const raw = import.meta.env.VITE_APP_MODE;
  if (raw == null || String(raw).trim() === '') return 'LAB';
  const u = String(raw).trim().toUpperCase();
  return u === 'PRODUCTION' ? 'PRODUCTION' : 'LAB';
};

const resolveLabel = (items, id, fallback) => {
  if (!id) return fallback;
  const found = items?.find((x) => String(x.key) === String(id));
  return found?.name || fallback || `ID ${id}`;
};

export const SessionProvider = ({ children }) => {
  const [appMode, setAppMode] = useState(resolveInitialAppMode);
  const [session, setSession] = useState(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [currentOperation, setCurrentOperation] = useState(null);
  const [switchError, setSwitchError] = useState(null);
  const [switchSuccess, setSwitchSuccess] = useState(null);
  const [unitCatalog, setUnitCatalog] = useState([]);
  const [sectorCatalog, setSectorCatalog] = useState([]);
  const unitCatalogRef = useRef(unitCatalog);
  const sectorCatalogRef = useRef(sectorCatalog);
  const lastSwitchRef = useRef(null);
  unitCatalogRef.current = unitCatalog;
  sectorCatalogRef.current = sectorCatalog;

  const fetchSession = useCallback(async () => {
    if (appMode === 'LAB') {
      setSession({
        prefecture: { id: '3128253', name: 'Guaraciama - MG' },
        unit: { id: '10', name: 'UBS SAO JOAO BATISTA PLANTOES' },
        sector: { id: '0', name: 'ATENDIMENTO' },
        user: { id: '1659', name: 'Administrador (Mock)', role: 'Gestor' },
        isValid: true,
      });
      setInitialLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/almox/v1/session/current`);
      const result = await response.json().catch(() => ({}));

      if (!response.ok) {
        const detail = result?.detail;
        const msg =
          typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
              ? detail.map((d) => d?.msg || d).join(' ')
              : result?.message || `HTTP ${response.status}`;
        setSwitchError(`Sessão Vivver: ${msg}`);
        return;
      }

      if (result?.data) {
        setSwitchError(null);
        setSession((prev) => {
          const last = lastSwitchRef.current;
          // /current pode atrasar vs. snapshot pós-switch; só ignorar se já temos sessão otimista.
          if (
            prev &&
            last &&
            Date.now() - last.at < 60_000 &&
            String(result.data.unit?.id) !== String(last.unitId)
          ) {
            return prev;
          }
          return mergeSessionLabels(prev, result.data, {
            unitCatalog: unitCatalogRef.current,
            sectorCatalog: sectorCatalogRef.current,
          });
        });
      } else {
        setSwitchError('Resposta do backend sem dados de contexto (`data` vazio).');
      }
    } catch (error) {
      console.error('Failed to fetch real session:', error);
      setSwitchError(
        `Não foi possível conectar ao backend em ${API_BASE}. Confirme VITE_API_URL e que o uvicorn está de pé — ver docs/OFFICIAL_LOCAL_PORTS.md`
      );
    } finally {
      setInitialLoading(false);
    }
  }, [appMode]);

  const fetchUnitCatalog = useCallback(async () => {
    if (appMode !== 'PRODUCTION') return;
    try {
      const res = await fetch(`${API_BASE}/almox/v1/session/available-units`);
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        console.warn('available-units HTTP', res.status, payload?.detail ?? payload);
        setUnitCatalog([]);
        return;
      }
      const list = Array.isArray(payload?.data) ? payload.data : [];
      setUnitCatalog(list);
    } catch (e) {
      console.error('Failed to load units', e);
      setUnitCatalog([]);
    }
  }, [appMode]);

  /** Sessão Vivver primeiro, depois catálogo — evita duas corrida ao Playwright em paralelo. */
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setInitialLoading(true);
      await fetchSession();
      if (cancelled) return;
      await fetchUnitCatalog();
    })();
    return () => {
      cancelled = true;
    };
  }, [appMode, fetchSession, fetchUnitCatalog]);

  // Enriquece labels quando o catálogo chega (sem re-fetch /current em loop)
  useEffect(() => {
    if (appMode !== 'PRODUCTION' || unitCatalog.length === 0 || !session) return;
    setSession((prev) => {
      if (!prev) return prev;
      const merged = mergeSessionLabels(prev, prev, {
        unitCatalog,
        sectorCatalog,
      });
      if (
        merged.unit?.name === prev.unit?.name &&
        merged.sector?.name === prev.sector?.name
      ) {
        return prev;
      }
      return merged;
    });
  }, [appMode, unitCatalog, sectorCatalog]);

  const updateUnit = (newUnit) => {
    setSession((prev) => ({
      ...prev,
      unit: newUnit,
      sector: { id: '', name: 'Selecione o Setor' },
    }));
  };

  const updateSector = (newSector) => {
    setSession((prev) => ({ ...prev, sector: newSector }));
  };

  const fetchSectorsForUnit = async (unitId) => {
    const res = await fetch(
      `${API_BASE}/almox/v1/session/available-sectors?unit_id=${encodeURIComponent(unitId)}`
    );
    const data = await res.json();
    const sectors = data.data || [];
    setSectorCatalog(sectors);
    return sectors;
  };

  const switchContext = async (unitId, sectorId = null) => {
    setSwitchError(null);
    setSwitchSuccess(null);

    if (appMode === 'LAB') {
      setSession((prev) => ({
        ...prev,
        unit: {
          id: unitId,
          name: resolveLabel(unitCatalog, unitId, `Unidade ${unitId} (Lab)`),
        },
        sector: sectorId
          ? {
              id: sectorId,
              name: resolveLabel(sectorCatalog, sectorId, `Setor ${sectorId}`),
            }
          : prev.sector,
      }));
      return true;
    }

    const sectorParam = sectorId ?? 'AUTO_RESOLVE';

    setCurrentOperation({
      status: 'SWITCHING',
      message: 'Troca no Vivver em andamento (pode levar até 1 min)...',
    });

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), SWITCH_TIMEOUT_MS);

    try {
      const response = await fetch(
        `${API_BASE}/almox/v1/session/switch?unit_id=${encodeURIComponent(unitId)}&sector_id=${encodeURIComponent(sectorParam)}`,
        { method: 'POST', signal: controller.signal }
      );
      clearTimeout(timeoutId);
      const result = await response.json();
      const op = result.data;

      if (!response.ok || !op) {
        const msg = result.detail || result.message || 'Falha na troca';
        setSwitchError(typeof msg === 'string' ? msg : JSON.stringify(msg));
        setCurrentOperation(null);
        return false;
      }

      if (op.status === 'COMPLETED') {
        const meta = op.metadata || {};
        const snap = meta.snapshot_after || {};
        const targetUnitId = String(op.target_unit_id ?? unitId);
        const targetSectorId = String(
          op.target_sector_id ?? meta.sector_id ?? sectorId ?? ''
        );
        const unitName =
          op.unit_name ||
          snap.unit ||
          resolveLabel(unitCatalogRef.current, targetUnitId, null);
        const sectorName =
          op.sector_name ||
          snap.sector ||
          resolveLabel(sectorCatalogRef.current, targetSectorId, null);

        lastSwitchRef.current = {
          at: Date.now(),
          unitId: targetUnitId,
          sectorId: targetSectorId,
        };

        setSession((prev) => ({
          ...prev,
          unit: {
            id: targetUnitId,
            name: isWeakLabel(unitName)
              ? resolveLabel(unitCatalogRef.current, targetUnitId, prev?.unit?.name)
              : unitName,
          },
          sector: {
            id: targetSectorId,
            name: isWeakLabel(sectorName)
              ? resolveLabel(sectorCatalogRef.current, targetSectorId, prev?.sector?.name)
              : sectorName,
          },
        }));
        setSwitchSuccess(
          op.message ||
            `Troca concluída: ${unitName || targetUnitId} / ${sectorName || targetSectorId}`
        );
        setCurrentOperation(null);
        return true;
      }

      if (op.status === 'MULTIPLE_CHOICES_REQUIRED') {
        setSectorCatalog(op.metadata?.sectors || []);
        setSwitchError('Vários setores disponíveis — escolha no menu SETOR.');
        setCurrentOperation(null);
        return false;
      }

      setSwitchError(op.error || op.message || 'Troca rejeitada pelo ERP');
      setCurrentOperation(null);
      return false;
    } catch (error) {
      clearTimeout(timeoutId);
      console.error('Failed to initiate context switch:', error);
      const aborted = error?.name === 'AbortError';
      setSwitchError(
        aborted
          ? `Troca excedeu o tempo limite (~2 min). Verifique o backend em ${API_BASE} e tente de novo.`
          : `Backend inacessível em ${API_BASE}. Reinicie uvicorn (porta oficial 8000 — ver docs/OFFICIAL_LOCAL_PORTS.md).`
      );
      setCurrentOperation(null);
      return false;
    }
  };

  const cancelCurrentOperation = () => {
    setCurrentOperation(null);
    setSwitchError(null);
  };

  return (
    <SessionContext.Provider
      value={{
        session,
        loading: initialLoading,
        initialLoading,
        appMode,
        currentOperation,
        switchError,
        setSwitchError,
        switchSuccess,
        unitCatalog,
        sectorCatalog,
        updateUnit,
        updateSector,
        setAppMode,
        switchContext,
        fetchSectorsForUnit,
        refreshSession: fetchSession,
        clearSwitchError: () => setSwitchError(null),
        clearSwitchSuccess: () => setSwitchSuccess(null),
        cancelCurrentOperation,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};
