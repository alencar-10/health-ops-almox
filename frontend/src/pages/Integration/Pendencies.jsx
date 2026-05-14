import React, { useState, useEffect } from 'react';
import { 
  AlertCircle, 
  RefreshCw, 
  ChevronRight, 
  Clock, 
  CheckCircle2, 
  XCircle,
  Activity
} from 'lucide-react';
import './Pendencies.css';

const Pendencies = () => {
  const [pendencies, setPendencies] = useState([
    // Mock data for initial layout
    {
      id: '1',
      name: 'AMOXICILINA 500MG',
      sku: 'SKU-7721AB',
      integration_status: 'FAILED',
      created_at: '2026-05-13T12:00:00Z',
      intent_id: '6bdea5cc-9f68-42c8-ba74-8ffe19ee6e09'
    }
  ]);

  const [selectedIntent, setSelectedIntent] = useState(null);
  const [timeline, setTimeline] = useState([]);

  const fetchTimeline = (intent_id) => {
    // Simulated timeline for the Vertical Slice proof
    const mockTimeline = [
      { step: 'NORMALIZATION', status: 'SUCCESS', time: '12:00:01', duration: '45ms' },
      { step: 'CREATE_PRINCIPLE', status: 'SUCCESS', time: '12:00:05', duration: '1200ms' },
      { step: 'CREATE_PRODUCT', status: 'SUCCESS', time: '12:00:08', duration: '850ms' },
      { step: 'LINK_PRINCIPLE', status: 'FAILURE', time: '12:00:10', duration: '5000ms', error: 'ERP_TIMEOUT' }
    ];
    setTimeline(mockTimeline);
    setSelectedIntent(intent_id);
  };

  return (
    <div className="pendencies-page">
      <header className="page-header">
        <div className="title-group">
          <h1>Pendências de Integração</h1>
          <p>Monitore falhas e sincronize produtos com o Vivver ERP.</p>
        </div>
        <button className="refresh-btn">
          <RefreshCw size={18} />
          Atualizar Lista
        </button>
      </header>

      <div className="dashboard-grid">
        <section className="list-section">
          <div className="table-container">
            <table className="pendencies-table">
              <thead>
                <tr>
                  <th>Produto</th>
                  <th>Status</th>
                  <th>Data Criado</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {pendencies.map(p => (
                  <tr key={p.id} className={selectedIntent === p.intent_id ? 'active' : ''}>
                    <td>
                      <div className="product-info">
                        <span className="p-name">{p.name}</span>
                        <span className="p-sku">{p.sku}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`status-badge ${p.integration_status.toLowerCase()}`}>
                        {p.integration_status}
                      </span>
                    </td>
                    <td>
                      <span className="date-cell">13/05/2026 12:00</span>
                    </td>
                    <td>
                      <button className="action-btn" onClick={() => fetchTimeline(p.intent_id)}>
                        <Activity size={16} />
                        Timeline
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="forensic-drawer">
          {selectedIntent ? (
            <div className="drawer-content">
              <h3>Timeline Forense</h3>
              <p className="intent-label">ID: {selectedIntent}</p>
              
              <div className="vertical-timeline">
                {timeline.map((step, idx) => (
                  <div key={idx} className={`timeline-item ${step.status.toLowerCase()}`}>
                    <div className="timeline-icon">
                      {step.status === 'SUCCESS' ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                    </div>
                    <div className="timeline-info">
                      <div className="step-header">
                        <span className="step-name">{step.step}</span>
                        <span className="step-time">{step.time}</span>
                      </div>
                      <div className="step-meta">
                        <Clock size={12} />
                        <span>{step.duration}</span>
                        {step.error && <span className="error-tag">{step.error}</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="drawer-actions">
                <button className="retry-main-btn">
                  <RefreshCw size={18} />
                  Executar Retry Manual
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-drawer">
              <AlertCircle size={48} color="#e2e8f0" />
              <p>Selecione um item para ver o rastro forense.</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
};

export default Pendencies;
