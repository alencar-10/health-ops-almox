import React, { useState } from 'react';
import { 
  Package, 
  ChevronDown, 
  LayoutDashboard, 
  Database, 
  ArrowLeftRight, 
  Settings, 
  ClipboardCheck,
  Truck,
  AlertCircle,
  FlaskConical,
  RefreshCcw
} from 'lucide-react';
import './Sidebar.css';

const Sidebar = ({ onViewChange, activeView }) => {
  const [openSections, setOpenSections] = useState({
    catalog: true,
    inbound: true,
    operation: false,
    logistics: false
  });

  const toggleSection = (section) => {
    setOpenSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  return (
    <aside className="sidebar" style={{ gridArea: 'sidebar' }}>
      <div className="logo-area">
        <div className="logo-box">
          <Package size={24} color="#fff" />
        </div>
        <span className="logo-text">HealthOps</span>
      </div>

      <nav className="nav-container">
        
        {/* 1. CATALOG SECTION */}
        <div className={`nav-section ${openSections.catalog ? 'open' : ''}`}>
          <button className="section-header" onClick={() => toggleSection('catalog')}>
            <div className="section-title">
              <Database size={18} />
              <span>Catálogo (Base)</span>
            </div>
            <ChevronDown size={14} className="chevron" />
          </button>
          <div className="section-content">
            <div 
              className={`nav-item ${activeView === 'products' ? 'active' : ''}`}
              onClick={() => onViewChange('products')}
            >
              <div className="nav-label-stack">
                <span className="nav-main">Cadastro de Produtos</span>
              </div>
            </div>
            <div 
              className={`nav-item ${activeView === 'principles' ? 'active' : ''}`}
              onClick={() => onViewChange('principles')}
            >
              <div className="nav-label-stack">
                <span className="nav-main">Cadastro de Princípios Ativos</span>
              </div>
            </div>
            <div className="nav-item">
              <div className="nav-label-stack">
                <span className="nav-main">Cadastro Completo</span>
              </div>
            </div>
            <div className="nav-item">
              <div className="nav-label-stack">
                <span className="nav-main">Cadastro de Fabricante</span>
              </div>
            </div>
            <div className="nav-item">
              <div className="nav-label-stack">
                <span className="nav-main">Cadastro de Fornecedor</span>
              </div>
            </div>
          </div>
        </div>

        {/* 2. INBOUND SECTION */}
        <div className={`nav-section ${openSections.inbound ? 'open' : ''}`}>
          <button className="section-header" onClick={() => toggleSection('inbound')}>
            <div className="section-title">
              <ArrowLeftRight size={18} />
              <span>Recebimento</span>
            </div>
            <ChevronDown size={14} className="chevron" />
          </button>
          <div className="section-content">
            <div 
              className={`nav-item ${activeView === 'direct_inbound' ? 'active' : ''}`}
              onClick={() => onViewChange('direct_inbound')}
            >
              Entrada Direta (Manual)
            </div>
            <div className="nav-item">
              Nota Fiscal
            </div>
            <div 
              className={`nav-item ${activeView === 'reconciliation' ? 'active' : ''}`}
              onClick={() => onViewChange('reconciliation')}
            >
              Nota Fiscal (XML) <span className="beta-tag">Beta</span>
            </div>
          </div>
        </div>

        {/* 3. OPERATION SECTION */}
        <div className={`nav-section ${openSections.operation ? 'open' : ''}`}>
          <button className="section-header" onClick={() => toggleSection('operation')}>
            <div className="section-title">
              <ClipboardCheck size={18} />
              <span>Operação</span>
            </div>
            <ChevronDown size={14} className="chevron" />
          </button>
          <div className="section-content">
            <div className="nav-item">Estoque</div>
            <div className="nav-item">Inventário</div>
          </div>
        </div>

        <div className="nav-divider" />

        <div className="nav-item single">
          <AlertCircle size={18} />
          <span>Pendências</span>
          <span className="badge">5</span>
        </div>

        <div className="nav-item single">
          <Settings size={18} />
          <span>Configurações</span>
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;
