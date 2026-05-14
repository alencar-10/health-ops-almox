import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Plus, 
  Filter, 
  MoreVertical, 
  ExternalLink,
  Database,
  FlaskConical,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import './Catalog.css';

const PrinciplesList = () => {
  const [principles, setPrinciples] = useState([
    { id: '1', name: "DIPIRONA SODICA", dose: "500MG/ML", form: "SOLUÇÃO ORAL", external_id: "VIV-9981", status: "SYNCED" },
    { id: '2', name: "AMOXICILINA", dose: "500MG", form: "COMPRIMIDO", external_id: null, status: "LOCAL_ONLY" },
    { id: '3', name: "PARACETAMOL", dose: "750MG", form: "COMPRIMIDO", external_id: "VIV-4421", status: "SYNCED" },
  ]);

  return (
    <div className="catalog-page">
      <header className="page-header">
        <div>
          <h1>Princípios Ativos</h1>
          <p>Gestão de substâncias e composições químicas no catálogo.</p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary">
            <Database size={18} />
            Importar Planilha
          </button>
          <button className="btn-primary">
            <Plus size={18} />
            Novo Princípio
          </button>
        </div>
      </header>

      <div className="filter-bar">
        <div className="search-input">
          <Search size={18} />
          <input type="text" placeholder="Buscar por nome ou código..." />
        </div>
        <button className="btn-filter">
          <Filter size={18} />
          Filtros
        </button>
      </div>

      <div className="catalog-grid">
        <table className="data-table">
          <thead>
            <tr>
              <th>Nome / Composição</th>
              <th>Forma Farmacêutica</th>
              <th>ID Vivver</th>
              <th>Status</th>
              <th className="text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            {principles.map(p => (
              <tr key={p.id}>
                <td>
                  <div className="item-name-cell">
                    <FlaskConical size={18} className="icon-subtle" />
                    <div>
                      <span className="main-name">{p.name}</span>
                      <span className="sub-name">{p.dose}</span>
                    </div>
                  </div>
                </td>
                <td>{p.form}</td>
                <td>
                  {p.external_id ? (
                    <span className="external-code mono">{p.external_id}</span>
                  ) : (
                    <span className="not-linked">Não vinculado</span>
                  )}
                </td>
                <td>
                  <div className={`status-badge ${p.status.toLowerCase()}`}>
                    {p.status === 'SYNCED' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
                    {p.status === 'SYNCED' ? 'Sincronizado' : 'Pendente ERP'}
                  </div>
                </td>
                <td className="text-right">
                  <div className="row-actions">
                    <button className="icon-btn" title="Ver no Vivver">
                      <ExternalLink size={18} />
                    </button>
                    <button className="icon-btn">
                      <MoreVertical size={18} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PrinciplesList;
