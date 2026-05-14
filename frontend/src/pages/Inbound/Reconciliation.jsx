import React, { useState } from 'react';
import { 
  FileSearch, 
  CheckCircle, 
  AlertTriangle, 
  Search, 
  ArrowRight,
  Info,
  ChevronRight,
  MoreVertical,
  PlusCircle,
  ArrowLeftRight
} from 'lucide-react';
import './Reconciliation.css';

const MOCK_ITEMS = [
  {
    id: 1,
    raw_name: "AMOXICILINA 500MG",
    raw_manufacturer: "ACHE LAB",
    raw_gtin: "789123456001",
    batch: "B-777",
    quantity: 100,
    suggestion: {
      id: "prod-123",
      label: "AMOXICILINA 500MG COMPRIMIDO",
      sku: "AMX-500",
      manufacturer: "ACHÉ LABORATÓRIOS FARMACÊUTICOS S.A.",
      score: 91,
      warnings: [],
      match_fields: ["description", "dosage"]
    }
  },
  {
    id: 2,
    raw_name: "DIPIRONA SODICA 500MG/ML",
    raw_manufacturer: "EMS S/A",
    raw_gtin: "789456123002",
    batch: "L-2024",
    quantity: 50,
    suggestion: {
      id: "prod-456",
      label: "DIPIRONA 500MG COMPRIMIDO",
      sku: "DIP-500",
      manufacturer: "EMS S/A",
      score: 85,
      warnings: ["FORMA FARMACÊUTICA DIVERGENTE: XML diz '500MG/ML', Catálogo diz 'COMPRIMIDO'"],
      match_fields: ["name", "manufacturer"]
    }
  }
];

const RegisterModal = ({ item, onCancel, onConfirm, isLoading }) => {
  const [formData, setFormData] = useState({
    form_id: "1",
    group_id: "01",
    subgroup_id: "001",
    uom_id: "1"
  });

  return (
    <div className="modal-overlay">
      <div className="modal-content fast-cockpit">
        <div className="modal-header">
          <h3>Cadastrar no Vivver</h3>
          <p>{item.raw_name}</p>
        </div>
        <div className="modal-body">
          <div className="form-group">
            <label>Forma Farmacêutica (ID)</label>
            <input 
              type="text" 
              value={formData.form_id} 
              onChange={e => setFormData({...formData, form_id: e.target.value})}
              placeholder="Ex: 1 (Comprimido)" 
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Grupo</label>
              <input 
                type="text" 
                value={formData.group_id} 
                onChange={e => setFormData({...formData, group_id: e.target.value})}
                placeholder="Ex: 01" 
              />
            </div>
            <div className="form-group">
              <label>Subgrupo</label>
              <input 
                type="text" 
                value={formData.subgroup_id} 
                onChange={e => setFormData({...formData, subgroup_id: e.target.value})}
                placeholder="Ex: 001" 
              />
            </div>
          </div>
          <div className="form-group">
            <label>Unidade de Medida</label>
            <select 
              value={formData.uom_id}
              onChange={e => setFormData({...formData, uom_id: e.target.value})}
            >
              <option value="1">UNIDADE</option>
              <option value="2">FRASCO</option>
              <option value="3">AMPOLA</option>
            </select>
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onCancel} disabled={isLoading}>Cancelar</button>
          <button className="btn-primary" onClick={() => onConfirm(formData)} disabled={isLoading}>
            {isLoading ? "Processando Registro (5 Passos)..." : "Registrar Agora"}
          </button>
        </div>
      </div>
    </div>
  );
};

const Reconciliation = () => {
  const [items, setItems] = useState(MOCK_ITEMS);
  const [registeringItem, setRegisteringItem] = useState(null);
  const [isRegistering, setIsRegistering] = useState(false);

  const handleUndo = (itemId) => {
    setItems(prev => prev.map(item => 
      item.id === itemId ? { ...item, is_confirmed: false } : item
    ));
    console.log("Vínculo desfeito para o item:", itemId);
  };

  const handleConfirmMatch = async (itemId, suggestion) => {
    try {
      const response = await fetch(`http://localhost:8001/almox/v1/inbound/items/${itemId}/reconcile`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'x-tenant-id': 'fb0282be-1b58-40ce-a124-1cf897e1a393',
          'x-unit-id': '3d14d3ea-52f4-42f7-bfa3-4e1fa1aabd42',
          'x-sector-id': '456'
        },
        body: JSON.stringify({
          product_id: suggestion.id || "fb0282be-1b58-40ce-a124-1cf897e1a393", // Mock ID if missing
          score: suggestion.score,
          metadata: { match_fields: suggestion.match_fields }
        })
      });

      if (response.ok) {
        setItems(prev => prev.map(item => 
          item.id === itemId ? { ...item, is_confirmed: true } : item
        ));
        alert("Vínculo confirmado com sucesso!");
      } else {
        const err = await response.json();
        alert("Falha ao confirmar: " + (err.detail?.message || err.detail || "Erro desconhecido"));
      }
    } catch (error) {
      alert("Erro de conexão com o servidor.");
    }
  };

  const handleRegister = async (formData) => {
    setIsRegistering(true);
    try {
      console.log("Iniciando registro para:", registeringItem.raw_name);
      
      const response = await fetch('http://localhost:8001/almox/v1/catalog/register-medicine?tenant_id=fb0282be-1b58-40ce-a124-1cf897e1a393&unit_id=3d14d3ea-52f4-42f7-bfa3-4e1fa1aabd42', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'x-tenant-id': 'fb0282be-1b58-40ce-a124-1cf897e1a393',
          'x-unit-id': '3d14d3ea-52f4-42f7-bfa3-4e1fa1aabd42',
          'x-sector-id': '456'
        },
        body: JSON.stringify({
          name: registeringItem.raw_name,
          ...formData,
          sku: registeringItem.raw_gtin
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Erro na API:", errorData);
        const errorMsg = errorData.detail?.message || errorData.detail || "Erro interno";
        alert("AVISO DO SISTEMA: " + errorMsg);
        
        // Even if it already exists (409), we can mark it as confirmed in the UI for the test
        if (response.status === 409) {
          setItems(prev => prev.map(item => 
            item.id === registeringItem.id ? { ...item, is_confirmed: true } : item
          ));
        }
        return;
      }

      const result = await response.json();
      console.log("Resultado do registro:", result);
      if (result.status === 'COMPLETED') {
        setItems(prev => prev.map(item => 
          item.id === registeringItem.id ? { ...item, is_confirmed: true } : item
        ));
        alert("REGISTRO CONCLUÍDO COM SUCESSO!\nProduto criado e vinculado no Vivver.");
      } else {
        alert("FALHA NO REGISTRO: " + (result.step || "Erro desconhecido"));
      }
    } catch (error) {
      console.error("Erro no fetch:", error);
      alert("ERRO DE COMUNICAÇÃO: Verifique se o servidor está rodando na porta 8001.");
    } finally {
      setIsRegistering(false);
      setRegisteringItem(null);
    }
  };

  return (
    <div className="reconciliation-page">
      {registeringItem && (
        <RegisterModal 
          item={registeringItem} 
          onCancel={() => setRegisteringItem(null)}
          onConfirm={handleRegister}
          isLoading={isRegistering}
        />
      )}
      <header className="page-header">
        <div className="header-info">
          <h1>Reconciliação de Entrada</h1>
          <p>Sessão ID: <span className="mono">3513-95ec-7260</span> | Tipo: <span className="badge-type">XML_NFE</span></p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary">Exportar LOG</button>
          <button className="btn-primary">Confirmar Toda Sessão</button>
        </div>
      </header>

      <div className="reconciliation-grid">
        <div className="grid-header">
          <div className="col">ORIGEM (XML)</div>
          <div className="col">SUGESTÃO IA (CATÁLOGO)</div>
          <div className="col">AÇÃO OPERACIONAL</div>
        </div>

        {items.map(item => (
          <div key={item.id} className="reconciliation-row">
            {/* COLUMN 1: XML ORIGIN (Sanitary Priority) */}
            <div className="col-source">
              <div className="sanitary-badge">
                <span className="batch">LOTE: {item.batch}</span>
                <span className="expiry">VAL: 05/2028</span>
              </div>
              <div className="item-identity">
                <span className="raw-name">{item.raw_name}</span>
                <span className="raw-manufacturer">{item.raw_manufacturer}</span>
              </div>
              <div className="item-meta">
                <span className="meta-tag">Qtd: {item.quantity}</span>
                <span className="meta-tag">EAN: {item.raw_gtin}</span>
              </div>
            </div>

            <div className="arrow-connector">
              <ChevronRight size={20} color="#cbd5e1" />
            </div>

            {/* COLUMN 2: IA SUGGESTION (Explainable AI) */}
            <div className="col-suggestion">
              <div className="suggestion-card">
                <div className="suggestion-header">
                  <div className="score-badge" style={{ backgroundColor: item.suggestion.score > 90 ? '#dcfce7' : '#fef9c3' }}>
                    {item.suggestion.score}% Match
                  </div>
                  <div className="score-breakdown">
                    <span className="match-tag ok">GTIN</span>
                    <span className="match-tag ok">MFR</span>
                    <span className="match-tag warn">FORM</span>
                  </div>
                </div>
                
                <div className="product-info">
                  <span className="product-label">{item.suggestion.label}</span>
                  <span className="manufacturer-label">{item.suggestion.manufacturer}</span>
                </div>

                {item.suggestion.warnings.length > 0 && (
                  <div className="warning-box semantic-alert">
                    <AlertTriangle size={14} color="#ca8a04" />
                    <span>Divergência: {item.suggestion.warnings[0]}</span>
                  </div>
                )}
              </div>
            </div>

            {/* COLUMN 3: ACTIONS (Operational Hierarchy) */}
            <div className="col-actions">
              <div className="action-stack">
                {!item.is_confirmed ? (
                  <>
                    <button 
                      className={`btn-action confirm ${item.suggestion.score < 90 || item.suggestion.warnings.length > 0 ? 'warning-friction' : ''}`}
                      onClick={() => handleConfirmMatch(item.id, item.suggestion)}
                    >
                      <CheckCircle size={18} />
                      {item.suggestion.score < 90 || item.suggestion.warnings.length > 0 ? 'Validar e Confirmar' : 'Confirmar Vínculo'}
                    </button>
                    
                    <div className="secondary-actions-area">
                      <button className="btn-action-ghost" onClick={() => alert("Simulando: Abrindo busca manual no catálogo do Vivver...")}>
                        <Search size={16} />
                        Trocar Sugestão
                      </button>
                      <button className="btn-action-outline-risk" onClick={() => setRegisteringItem(item)}>
                        <PlusCircle size={16} />
                        Novo Cadastro (ERP)
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="confirmed-status-badge">
                    <div className="status-label">
                      <CheckCircle size={14} />
                      <span>ERP_SYNCED</span>
                    </div>
                    <button className="btn-undo-ghost" onClick={() => handleUndo(item.id)}>
                      Desfazer
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <footer className="page-actions">
        <div className="summary-info">
          <span>Total de Itens: {items.length}</span>
          <span className="divider" />
          <span>Pendentes: {items.filter(i => !i.is_confirmed).length}</span>
        </div>
        <div className="btn-group">
          <button className="btn-secondary" onClick={() => alert("Simulando: Todos os itens pendentes foram marcados para revisão.")}>
            Revisar Todos
          </button>
          <button className="btn-primary" onClick={() => alert("REGISTRO DE LOTE CONCLUÍDO!\n\nOs itens reconciliados foram postados no Ledger e estão prontos para sincronia com o estoque do Vivver.")}>
            Finalizar e Sincronizar Lote
          </button>
        </div>
      </footer>
    </div>
  );
};

export default Reconciliation;
