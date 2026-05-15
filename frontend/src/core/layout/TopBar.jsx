import React, { useState, useEffect, useRef } from 'react';
import {
  MapPin,
  Hospital,
  Users,
  User,
  ShieldCheck,
  CheckCircle2,
  ChevronDown,
} from 'lucide-react';
import { API_BASE } from '../config/apiBase';
import { useSession } from '../context/SessionContext';
import { isWeakLabel } from '../context/sessionMerge';
import './TopBar.css';

const TopBar = () => {
  const {
    session,
    appMode,
    setAppMode,
    switchContext,
    currentOperation,
    switchError,
    setSwitchError,
    switchSuccess,
    unitCatalog,
    sectorCatalog,
    fetchSectorsForUnit,
    clearSwitchError,
    clearSwitchSuccess,
  } = useSession();
  const [showUnits, setShowUnits] = useState(false);
  const [showSectors, setShowSectors] = useState(false);
  const [showTenants, setShowTenants] = useState(false);
  const [availableUnits, setAvailableUnits] = useState([]);
  const [availableSectors, setAvailableSectors] = useState([]);
  const [sectorsUnitId, setSectorsUnitId] = useState(null);
  const [switching, setSwitching] = useState(false);
  const topBarRef = useRef(null);
  /** Unidades no painel ≠ “lista vazio” ⇒ loading infinito */
  const [unitsBusy, setUnitsBusy] = useState(false);
  const [unitsFetchErr, setUnitsFetchErr] = useState('');
  const [sectorsBusy, setSectorsBusy] = useState(false);
  const [sectorsFetchErr, setSectorsFetchErr] = useState('');

  const busy = Boolean(currentOperation) || switching;

  useEffect(() => {
    if (!showUnits && !showSectors && !showTenants) return;
    const onPointerDown = (e) => {
      if (topBarRef.current && !topBarRef.current.contains(e.target)) {
        setShowUnits(false);
        setShowSectors(false);
        setShowTenants(false);
      }
    };
    document.addEventListener('pointerdown', onPointerDown, true);
    return () => document.removeEventListener('pointerdown', onPointerDown, true);
  }, [showUnits, showSectors, showTenants]);

  /** Catálogo chegou pelo SessionProvider — atualiza lista se dropdown aberto. */
  useEffect(() => {
    if (!showUnits || appMode !== 'PRODUCTION') return;
    if (unitCatalog.length > 0) {
      setAvailableUnits(unitCatalog);
      setUnitsBusy(false);
      setUnitsFetchErr('');
    }
  }, [showUnits, appMode, unitCatalog]);

  /** Busca explícita ao abrir, se contexto ainda não tem lista (ou catálogo vazio legítimo após erro). */
  useEffect(() => {
    if (!showUnits || appMode !== 'PRODUCTION') return;

    if (unitCatalog.length > 0) {
      return;
    }

    let cancelled = false;
    const ac = new AbortController();
    const tm = window.setTimeout(() => ac.abort(), 120_000);

    setUnitsBusy(true);
    setUnitsFetchErr('');

    fetch(`${API_BASE}/almox/v1/session/available-units`, { signal: ac.signal })
      .then(async (res) => {
        window.clearTimeout(tm);
        if (cancelled) return;
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          const d = body?.detail;
          const msg =
            typeof d === 'string'
              ? d
              : Array.isArray(d)
                ? d.map((x) => x?.msg || x).join(' ')
                : JSON.stringify(body);
          throw new Error(msg || `HTTP ${res.status}`);
        }
        const list = Array.isArray(body?.data) ? body.data : [];
        setAvailableUnits(list);
      })
      .catch((err) => {
        window.clearTimeout(tm);
        if (cancelled) return;
        const aborted = ac.signal.aborted || err?.name === 'AbortError';
        if (aborted) {
          setUnitsFetchErr(
            'Tempo limite (>2 min) ao carregar unidades. Backend/Vivver em carga ou indisponível.'
          );
          return;
        }
        setUnitsFetchErr(err?.message || 'Falha ao carregar unidades.');
        setAvailableUnits([]);
      })
      .finally(() => {
        window.clearTimeout(tm);
        if (!cancelled) setUnitsBusy(false);
      });

    return () => {
      cancelled = true;
      window.clearTimeout(tm);
      ac.abort();
    };
  }, [showUnits, appMode, unitCatalog]);

  useEffect(() => {
    if (!showSectors || appMode !== 'PRODUCTION' || busy) return;

    const unitId = sectorsUnitId || session?.unit?.id;
    if (!unitId) {
      setSectorsFetchErr('Selecione uma unidade antes do setor.');
      setAvailableSectors([]);
      return;
    }

    if (sectorCatalog.length > 0) {
      setAvailableSectors(sectorCatalog);
      setSectorsBusy(false);
      setSectorsFetchErr('');
      return;
    }

    let dead = false;
    setSectorsBusy(true);
    setSectorsFetchErr('');

    fetchSectorsForUnit(unitId)
      .then((list) => {
        if (dead) return;
        const arr = Array.isArray(list) ? list : [];
        setAvailableSectors(arr);
      })
      .catch((e) => {
        if (dead) return;
        setSectorsFetchErr(e?.message || String(e));
        setAvailableSectors([]);
      })
      .finally(() => {
        if (!dead) setSectorsBusy(false);
      });

    return () => {
      dead = true;
    };
  }, [showSectors, appMode, busy, sectorsUnitId, session?.unit?.id, sectorCatalog, fetchSectorsForUnit]);

  const toggleMode = () => setAppMode((prev) => (prev === 'LAB' ? 'PRODUCTION' : 'LAB'));

  const handleUnitSwitch = async (unit) => {
    if (currentOperation || switching) return;
    clearSwitchError();
    setShowUnits(false);
    setSectorsUnitId(unit.key);
    setSwitching(true);
    try {
      const sectors = await fetchSectorsForUnit(unit.key);
      setAvailableSectors(sectors);
      if (sectors.length === 1) {
        await switchContext(unit.key, sectors[0].key);
        return;
      }
      if (sectors.length > 1) {
        setShowSectors(true);
        return;
      }
      await switchContext(unit.key);
    } finally {
      setSwitching(false);
    }
  };

  const handleSectorSwitch = async (sector) => {
    if (currentOperation || switching) return;
    if (!sectorsUnitId) {
      setSwitchError('Selecione a unidade novamente antes do setor.');
      return;
    }
    clearSwitchError();
    setShowSectors(false);
    setSwitching(true);
    const unitId = sectorsUnitId;
    try {
      await switchContext(unitId, sector.key);
    } finally {
      setSwitching(false);
    }
  };

  if (!session) {
    return (
      <header className="top-bar top-bar--session-pending">
        <div className="context-group">
          <span className="top-bar-session-pending">
            {appMode === 'PRODUCTION'
              ? 'Contexto Vivver não carregado — verifique backend e sessão ERP.'
              : 'Carregando contexto da sessão...'}
          </span>
        </div>
        <div className="status-indicators">
          {switchError && (
            <div className="status-badge failed" title={switchError}>
              ⚠️ <span>{switchError}</span>
            </div>
          )}
          <div
            className={`status-badge ${(appMode || 'LAB').toLowerCase()} clickable`}
            onClick={toggleMode}
          >
            <ShieldCheck size={14} />
            <span>
              {appMode === 'PRODUCTION'
                ? 'VIVVER PRODUCTION MODE (REAL)'
                : 'HEALTH-OPS LAB MODE (SIMULATION)'}
            </span>
          </div>
        </div>
      </header>
    );
  }

  const displayUnitName = isWeakLabel(session.unit?.name)
    ? unitCatalog.find((u) => String(u.key) === String(session.unit?.id))?.name ||
      session.unit?.name
    : session.unit?.name;

  const displaySectorName = isWeakLabel(session.sector?.name)
    ? sectorCatalog.find((s) => String(s.key) === String(session.sector?.id))?.name ||
      session.sector?.name
    : session.sector?.name;

  return (
    <header className="top-bar" ref={topBarRef}>
      <div className="context-group">
        <div
          className="context-item clickable"
          onClick={() => {
            setShowUnits(false);
            setShowSectors(false);
            setShowTenants((v) => !v);
          }}
        >
          <span className="context-label">PREFEITURA</span>
          <div className="context-value">
            <MapPin size={14} className="icon-blue" />
            <span>{session.prefecture.name}</span>
            <ChevronDown size={14} style={{ marginLeft: '4px', opacity: 0.6 }} />
          </div>
        </div>

        <div className="context-divider" />

        <div
          className={`context-item ${busy ? 'disabled' : 'clickable'}`}
          onClick={() => {
            if (busy) return;
            setShowTenants(false);
            setShowSectors(false);
            setShowUnits((v) => !v);
          }}
        >
          <span className="context-label">UNIDADE DE SAÚDE</span>
          <div className="context-value">
            <Hospital size={14} className="icon-blue" />
            <span>{displayUnitName}</span>
            <ChevronDown size={14} style={{ marginLeft: '4px', opacity: 0.6 }} />
          </div>
          {showUnits && !busy && (
            <div className="units-dropdown">
              <div className="dropdown-header">Selecionar Unidade (Real)</div>
              {unitsBusy && availableUnits.length === 0 ? (
                <div className="dropdown-loading">
                  Carregando unidades… A primeira chamada pode levar 30–90s (Vivver/Playwright).
                </div>
              ) : unitsFetchErr ? (
                <div className="dropdown-msg dropdown-msg--error">{unitsFetchErr}</div>
              ) : availableUnits.length === 0 ? (
                <div className="dropdown-msg">
                  Nenhuma unidade disponível para este operador nesta sessão. Verifique permissões no Vivver
                  ou as credenciais do backend.
                </div>
              ) : (
                availableUnits.map((u) => (
                  <div
                    key={u.key}
                    className={`dropdown-item ${String(session?.unit?.id) === String(u.key) ? 'active' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleUnitSwitch(u);
                    }}
                  >
                    {u.name}
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <div className="context-divider" />

        <div
          className={`context-item ${busy ? 'disabled' : 'clickable'}`}
          onClick={() => {
            if (busy) return;
            setShowTenants(false);
            setShowUnits(false);
            setShowSectors((v) => !v);
          }}
        >
          <span className="context-label">SETOR</span>
          <div className="context-value">
            <Users size={14} className="icon-blue" />
            <span>{displaySectorName}</span>
            <ChevronDown size={14} style={{ marginLeft: '4px', opacity: 0.6 }} />
          </div>
          {showSectors && !busy && (
            <div className="units-dropdown">
              <div className="dropdown-header">Selecionar Setor</div>
              {sectorsBusy && availableSectors.length === 0 ? (
                <div className="dropdown-loading">Carregando setores…</div>
              ) : sectorsFetchErr ? (
                <div className="dropdown-msg dropdown-msg--error">{sectorsFetchErr}</div>
              ) : availableSectors.length === 0 ? (
                <div className="dropdown-msg">Nenhum setor retornado para esta unidade.</div>
              ) : (
                availableSectors.map((s) => (
                  <div
                    key={s.key}
                    className={`dropdown-item ${String(session?.sector?.id) === String(s.key) ? 'active' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSectorSwitch(s);
                    }}
                  >
                    {s.name}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      <div className="status-indicators">
        {switchError && (
          <div className="status-badge failed" title={switchError}>
            ⚠️ <span>{switchError}</span>
          </div>
        )}
        {currentOperation && (
          <div
            className={`status-badge op-pulse ${
              ['FAILED', 'MULTIPLE_CHOICES_REQUIRED', 'TIMEOUT'].includes(currentOperation.status)
                ? 'failed'
                : 'processing'
            }`}
          >
            {currentOperation.status === 'FAILED' ? '⚠️ ' : '🔄 '}
            <span>{currentOperation.message}</span>
          </div>
        )}
        {!currentOperation && !switchError && (
          <div
            className="status-badge valid"
            title={switchSuccess || undefined}
            onClick={switchSuccess ? clearSwitchSuccess : undefined}
            role={switchSuccess ? 'button' : undefined}
          >
            <CheckCircle2 size={14} />
            <span>{switchSuccess || 'Contexto operacional válido'}</span>
          </div>
        )}
        <div
          className={`status-badge ${appMode.toLowerCase()} clickable`}
          onClick={toggleMode}
        >
          <ShieldCheck size={14} />
          <span>
            {appMode === 'PRODUCTION'
              ? 'VIVVER PRODUCTION MODE (REAL)'
              : 'HEALTH-OPS LAB MODE (SIMULATION)'}
          </span>
        </div>
      </div>

      <div className="user-profile">
        <div className="user-info">
          <span className="user-name">{session.user.name}</span>
          <span className="user-role">Perfil: {session.user.role}</span>
        </div>
        <div className="user-avatar">
          <User size={20} />
        </div>
      </div>
    </header>
  );
};

export default TopBar;
