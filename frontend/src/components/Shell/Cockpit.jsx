import React from 'react';
import { 
  Building2, 
  MapPin, 
  Search, 
  Bell, 
  User as UserIcon,
  CheckCircle2,
  ChevronDown,
  ShieldCheck,
  FlaskConical
} from 'lucide-react';
import './Cockpit.css';

const Cockpit = () => {
  // Mock environment (In a real app this would come from an environment variable)
  const appMode = "LAB"; // Switch to "PRODUCTION" to see the red banner
  const isProduction = appMode === "PRODUCTION";

  return (
    <header className="cockpit" style={{ gridArea: 'cockpit' }}>
      {/* Dynamic Environment Banner (ADR-015 Refinement) */}
      <div className={`env-banner ${isProduction ? 'production' : 'lab'}`}>
        <div className="banner-content">
          {isProduction ? <ShieldCheck size={14} className="pulse" /> : <FlaskConical size={14} />}
          <span>
            {isProduction 
              ? "VIVVER PRODUCTION MODE - LIVE ERP INTEGRATION ACTIVE" 
              : "HEALTH-OPS LAB MODE - SIMULATION & SAFETY ON"}
          </span>
        </div>
      </div>

      <div className="context-bar">
        <div className="operational-context-aggressive">
          <div className="context-item main">
            <label>PREFEITURA</label>
            <div className="context-value">
              <Building2 size={16} />
              <span>GUARACIAMA - MG</span>
              <ChevronDown size={14} />
            </div>
          </div>

          <div className="context-divider" />

          <div className="context-item">
            <label>UNIDADE</label>
            <div className="context-value">
              <MapPin size={16} />
              <span>ALMOXARIFADO CENTRAL</span>
              <ChevronDown size={14} />
            </div>
          </div>

          <div className="context-divider" />

          <div className="context-item">
            <label>OPERADOR</label>
            <div className="context-value mono">
              <UserIcon size={16} />
              <span>ADMIN_MGM</span>
            </div>
          </div>
        </div>

        <div className="status-indicator">
          <CheckCircle2 size={16} color="var(--success)" />
          <span>Sessão Válida</span>
        </div>
      </div>

      <div className="user-area">
        <button className="icon-btn">
          <Bell size={20} />
          <span className="dot" />
        </button>
        
        <div className="user-profile">
          <div className="avatar">
            <UserIcon size={20} />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Cockpit;
