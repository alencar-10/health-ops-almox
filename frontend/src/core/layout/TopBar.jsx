import React from 'react';
import { 
  MapPin, 
  Hospital, 
  Users, 
  User, 
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';
import { useSession } from '../context/SessionContext';
import './TopBar.css';

const TopBar = () => {
  const { session, appMode, setAppMode } = useSession();

  const toggleMode = () => {
    setAppMode(prev => prev === 'LAB' ? 'PRODUCTION' : 'LAB');
  };

  return (
    <header className="top-bar">
      <div className="context-group">
        <div className="context-item">
          <span className="context-label">PREFEITURA</span>
          <div className="context-value">
            <MapPin size={14} className="icon-blue" />
            <span>{session.prefecture.name}</span>
          </div>
        </div>

        <div className="context-divider" />

        <div className="context-item">
          <span className="context-label">UNIDADE DE SAÚDE</span>
          <div className="context-value">
            <Hospital size={14} className="icon-blue" />
            <span>{session.unit.name}</span>
          </div>
        </div>

        <div className="context-divider" />

        <div className="context-item">
          <span className="context-label">SETOR</span>
          <div className="context-value">
            <Users size={14} className="icon-blue" />
            <span>{session.sector.name}</span>
          </div>
        </div>
      </div>

      <div className="status-indicators">
        <div className="status-badge valid">
          <CheckCircle2 size={14} />
          <span>Contexto operacional válido</span>
        </div>
        
        <div 
          className={`status-badge ${appMode.toLowerCase()} clickable`}
          onClick={toggleMode}
          title="Clique para alternar entre Lab e Produção Real"
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
