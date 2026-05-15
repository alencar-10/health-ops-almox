import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Hospital,
  Users,
  User,
  ShieldCheck,
  CheckCircle2,
  ChevronDown,
} from 'lucide-react';
import { useSession } from '../context/SessionContext';
import { isWeakLabel } from '../context/sessionMerge';
import './TopBar.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

  useEffect(() => {
    if (unitCatalog.length > 0) setAvailableUnits(unitCatalog);
  }, [unitCatalog]);

  useEffect(() => {
    if (showUnits && appMode === 'PRODUCTION' && availableUnits.length === 0) {
      fetch(`${API_BASE}/almox/v1/session/available-units`)
        .then((res) => res.json())
        .then((result) => {
          if (result.data) setAvailableUnits(result.data);
        })
        .catch((err) => console.error('Error fetching units:', err));
    }
  }, [showUnits, appMode, availableUnits.length]);

  useEffect(() => {
    if (sectorCatalog.length > 0) setAvailableSectors(sectorCatalog);
  }, [sectorCatalog]);

  useEffect(() => {
    if (showSectors && appMode === 'PRODUCTION' && session?.unit?.id) {
      const unitId = sectorsUnitId || session.unit.id;
      fetchSectorsForUnit(unitId).then(setAvailableSectors);
    }
  }, [showSectors, appMode, session?.unit?.id, sectorsUnitId, fetchSectorsForUnit]);

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

  const busy = Boolean(currentOperation) || switching;

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
    <header className="top-bar">
      <div className="context-group">
        <div className="context-item clickable" onClick={() => setShowTenants(!showTenants)}>
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
          onClick={() => !busy && setShowUnits(!showUnits)}
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
              {availableUnits.length > 0 ? (
                availableUnits.map((u) => (
                  <div
                    key={u.key}
                    className={`dropdown-item ${String(session.unit.id) === String(u.key) ? 'active' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleUnitSwitch(u);
                    }}
                  >
                    {u.name}
                  </div>
                ))
              ) : (
                <div className="dropdown-loading">Carregando unidades (1ª vez ~30s)...</div>
              )}
            </div>
          )}
        </div>

        <div className="context-divider" />

        <div
          className={`context-item ${busy ? 'disabled' : 'clickable'}`}
          onClick={() => !busy && setShowSectors(!showSectors)}
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
              {availableSectors.length > 0 ? (
                availableSectors.map((s) => (
                  <div
                    key={s.key}
                    className={`dropdown-item ${String(session.sector.id) === String(s.key) ? 'active' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSectorSwitch(s);
                    }}
                  >
                    {s.name}
                  </div>
                ))
              ) : (
                <div className="dropdown-loading">Carregando setores...</div>
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
