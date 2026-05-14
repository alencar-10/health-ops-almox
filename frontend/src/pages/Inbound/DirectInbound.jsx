import React, { useState } from 'react';
import { 
  Plus, 
  Upload, 
  Trash2, 
  Save, 
  CheckCircle2, 
  AlertTriangle,
  ArrowDown,
  Search,
  RefreshCcw,
  X,
  Edit3,
  Brain,
  History,
  AlertCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Factory
} from 'lucide-react';
import './DirectInbound.css';

const DirectInbound = () => {
  const [isManualOpen, setIsManualOpen] = useState(false);
  const [drawerItem, setDrawerItem] = useState(null); // Item being resolved
  const [items, setItems] = useState([
    { id: 1, product: "ABAXADOR DE LINGUA", code: "11750", manufacturer: "3M", batch: "BATCH-001", expiry: "2029-05-31", qty: 100, price: 0.50, status: "OK" },
    { id: 2, product: "GAZE ESTERIL 7,5X7,5", code: "15501", manufacturer: "", batch: "", expiry: "", qty: 50, price: 0.15, status: "PENDING" },
    { id: 3, product: "DIPIRONA 500MG/ML", code: "99221", manufacturer: "MEDLEY", batch: "L22X9", expiry: "2025-10-12", qty: 200, price: 1.20, status: "LEARNED" },
  ]);

  const [form, setForm] = useState({
    product: '',
    manufacturer: '',
    batch: '',
    expiryDate: '',
    qty: 1,
    price: 0
  });

  const [editingCell, setEditingCell] = useState(null); // { id, field }
  const [isProcessing, setIsProcessing] = useState(false);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsProcessing(true);

    // Simulate Spreadsheet Processing Delay
    setTimeout(() => {
      const simulatedItems = [
        { id: Date.now() + 1, product: "SOLUCAO FISIOLOGICA 0,9%", code: "10020", manufacturer: "JP FARMA", batch: "BATCH-XL", expiry: "2026-12-30", qty: 500, price: 4.50, status: "OK" },
        { id: Date.now() + 2, product: "ALCOOL EM GEL 70%", code: "10035", manufacturer: "", batch: "LOTE-ALG", expiry: "2025-06-15", qty: 250, price: 12.00, status: "PENDING" },
        { id: Date.now() + 3, product: "MASCARA DESCARTAVEL", code: "10048", manufacturer: "DESCARPACK", batch: "", expiry: "", qty: 1000, price: 0.10, status: "ERROR" }
      ];

      setItems(prev => [...simulatedItems, ...prev]);
      setIsProcessing(false);
    }, 1500);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'OK': return <CheckCircle2 size={16} className="st-ok" />;
      case 'PENDING': return <AlertTriangle size={16} className="st-pending" />;
      case 'ERROR': return <X size={16} className="st-error" />;
      case 'REVIEW': return <HelpCircle size={16} className="st-review" />;
      case 'SYNCING': return <RefreshCcw size={16} className="st-syncing rotating" />;
      case 'LEARNED': return <Brain size={16} className="st-learned" />;
      default: return null;
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const handleUpdateItem = (itemId, field, value) => {
    setItems(prev => prev.map(item => 
      item.id === itemId ? { ...item, [field]: value } : item
    ));
    setEditingCell(null);
  };

  const handleAddItem = (e) => {
    e.preventDefault();
    const newItem = {
      id: Date.now(),
      product: form.product || "NOVO ITEM",
      code: "MNL",
      manufacturer: form.manufacturer || "N/A",
      batch: form.batch,
      expiry: form.expiryDate,
      qty: form.qty,
      price: form.price,
      status: "OK"
    };
    setItems([newItem, ...items]);
    setForm({
      product: '',
      manufacturer: '',
      batch: '',
      expiryDate: '',
      qty: 1,
      price: 0
    });
    setIsManualOpen(false);
  };

  return (
    <div className="direct-inbound-page">
      <header className="page-header">
        <div className="header-context">
          <h1>Entrada Direta de Produtos</h1>
          <div className="fixed-reason">
            <span className="label">Motivo de Entrada:</span>
            <span className="value">9 - ENTRADA INICIAL OU CONTAGEM DO ESTOQUE</span>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn-save-all" onClick={() => alert("Salvando lote atômico no Vivver...")}>
            <Save size={18} />
            Salvar Lote (Disquete)
          </button>
        </div>
      </header>

      {/* 1. IMPORT SECTION (Full Width) */}
      <section className="import-section">
        <div className={`import-box ${isProcessing ? 'processing' : ''}`}>
          {isProcessing ? (
            <div className="processing-loader">
              <RefreshCcw className="rotating" size={32} />
              <div className="import-text">
                <h3>Lendo Planilha...</h3>
                <p>O HealthOps está validando os dados com o catálogo local.</p>
              </div>
            </div>
          ) : (
            <>
              <Upload className="icon-upload" />
              <div className="import-text">
                <h3>Importar Planilha de Entrada</h3>
                <p>Arraste seu arquivo .xlsx ou .csv para processamento em massa</p>
              </div>
              <label className="btn-browse">
                Procurar Arquivo
                <input type="file" hidden onChange={handleFileUpload} accept=".xlsx,.csv" />
              </label>
            </>
          )}
        </div>
      </section>

      {/* 2. MANUAL ENTRY (Collapsible) */}
      <section className={`manual-section ${isManualOpen ? 'open' : ''}`}>
        <button className="manual-toggle" onClick={() => setIsManualOpen(!isManualOpen)}>
          <div className="toggle-label">
            <Plus size={18} />
            <span>Entrada Manual de Itens</span>
          </div>
          {isManualOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
        
        {isManualOpen && (
          <form className="manual-form-stacked" onSubmit={handleAddItem}>
            <div className="form-grid">
              <div className="form-group">
                <label>Produto</label>
                <div className="search-field">
                  <Search size={16} />
                  <input 
                    type="text" 
                    placeholder="Código ou Nome" 
                    value={form.product}
                    onChange={e => setForm({...form, product: e.target.value})} 
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Fabricante</label>
                <input 
                  type="text" 
                  placeholder="Buscar no catálogo local" 
                  value={form.manufacturer}
                  onChange={e => setForm({...form, manufacturer: e.target.value})} 
                />
              </div>
              <div className="form-group">
                <label>Lote</label>
                <input 
                  type="text" 
                  placeholder="Lote" 
                  value={form.batch}
                  onChange={e => setForm({...form, batch: e.target.value})} 
                />
              </div>
              <div className="form-group">
                <label>Validade</label>
                <input 
                  type="date" 
                  value={form.expiryDate}
                  onChange={e => setForm({...form, expiryDate: e.target.value})} 
                />
              </div>
              <div className="form-group">
                <label>Qtd</label>
                <input 
                  type="number" 
                  value={form.qty}
                  onChange={e => setForm({...form, qty: e.target.value})} 
                />
              </div>
              <div className="form-group">
                <label>Preço</label>
                <input 
                  type="number" 
                  step="0.01" 
                  placeholder="0,00" 
                  value={form.price}
                  onChange={e => setForm({...form, price: e.target.value})} 
                />
              </div>
            </div>
            <button type="submit" className="btn-confirm-manual">Adicionar à Grade</button>
          </form>
        )}
      </section>

      {/* 3. CONFERENCE GRID (Full Width) */}
      <section className="grid-section">
        <div className="grid-header">
          <div className="title-stack">
            <h3>Grade de Conferência</h3>
            <p>Revise os itens importados antes da sincronia final</p>
          </div>
          <div className="grid-actions">
            <button className="btn-secondary">
              <RefreshCcw size={14} />
              Sincronizar Catálogo Local
            </button>
            <span className="item-counter">{items.length} Itens</span>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="operational-table">
            <thead>
              <tr>
                <th width="100">Status</th>
                <th>Produto</th>
                <th>Fabricante</th>
                <th width="120">Lote</th>
                <th width="140">Validade</th>
                <th width="80">Qtd</th>
                <th width="120">Preço</th>
                <th width="100" className="text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map(item => (
                <tr key={item.id} className={`row-state-${item.status.toLowerCase()}`}>
                  <td>
                    <div className="status-badge">
                      {getStatusIcon(item.status)}
                      <span>{item.status}</span>
                    </div>
                  </td>
                  <td>
                    <div className="product-info">
                      <span className="name">{item.product}</span>
                      <span className="code">Cód: {item.code}</span>
                    </div>
                  </td>
                  <td className={!item.manufacturer ? 'td-error' : ''}>
                    {item.manufacturer || "NÃO IDENTIFICADO"}
                  </td>
                  <td 
                    className={`td-editable ${!item.batch ? 'td-error' : ''}`}
                    onClick={() => setEditingCell({ id: item.id, field: 'batch' })}
                  >
                    {editingCell?.id === item.id && editingCell?.field === 'batch' ? (
                      <input 
                        autoFocus
                        className="inline-edit-input"
                        onBlur={(e) => handleUpdateItem(item.id, 'batch', e.target.value)}
                        defaultValue={item.batch}
                      />
                    ) : (
                      <span>{item.batch || "Inserir Lote"}</span>
                    )}
                  </td>
                  <td 
                    className={`td-editable ${!item.expiry ? 'td-error' : ''}`}
                    onClick={() => setEditingCell({ id: item.id, field: 'expiry' })}
                  >
                    {editingCell?.id === item.id && editingCell?.field === 'expiry' ? (
                      <input 
                        type="date"
                        autoFocus
                        className="inline-edit-input"
                        onBlur={(e) => handleUpdateItem(item.id, 'expiry', e.target.value)}
                        defaultValue={item.expiry}
                      />
                    ) : (
                      <span>{item.expiry || "Inserir Validade"}</span>
                    )}
                  </td>
                  <td 
                    className="td-editable"
                    onClick={() => setEditingCell({ id: item.id, field: 'qty' })}
                  >
                    {editingCell?.id === item.id && editingCell?.field === 'qty' ? (
                      <input 
                        type="number"
                        autoFocus
                        className="inline-edit-input"
                        onBlur={(e) => handleUpdateItem(item.id, 'qty', e.target.value)}
                        defaultValue={item.qty}
                      />
                    ) : (
                      <strong>{item.qty}</strong>
                    )}
                  </td>
                  <td 
                    className="td-editable"
                    onClick={() => setEditingCell({ id: item.id, field: 'price' })}
                  >
                    {editingCell?.id === item.id && editingCell?.field === 'price' ? (
                      <input 
                        type="number"
                        step="0.01"
                        autoFocus
                        className="inline-edit-input"
                        onBlur={(e) => handleUpdateItem(item.id, 'price', e.target.value)}
                        defaultValue={item.price}
                      />
                    ) : (
                      <span>{formatCurrency(item.price)}</span>
                    )}
                  </td>
                  <td className="text-right actions-cell">
                    <button className="btn-resolver" onClick={() => setDrawerItem(item)}>
                      <Edit3 size={14} />
                    </button>
                    <button className="btn-delete" onClick={() => setItems(items.filter(i => i.id !== item.id))}>
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 4. SIDE DRAWER (Resolution Panel) */}
      {drawerItem && (
        <>
          <div className="drawer-overlay" onClick={() => setDrawerItem(null)} />
          <div className="resolution-drawer">
            <header className="drawer-header">
              <div className="title">
                <Edit3 size={18} />
                <h3>Resolver Item</h3>
              </div>
              <button className="close-btn" onClick={() => setDrawerItem(null)}>
                <X size={20} />
              </button>
            </header>

            <div className="drawer-body">
              <div className="imported-info">
                <label>Item Importado da Planilha:</label>
                <div className="info-card">
                  <p><strong>Nome:</strong> {drawerItem.product}</p>
                  <p><strong>Cód. Origem:</strong> {drawerItem.code}</p>
                </div>
              </div>

              <div className="resolution-form">
                <div className="field-group">
                  <label>Vincular ao Catálogo Local (Vivver)</label>
                  <div className="search-box">
                    <Search size={16} />
                    <input type="text" placeholder="Buscar no Catálogo Local..." autoFocus />
                  </div>
                  <p className="help-text">Pesquisa rápida na tabela local de produtos.</p>
                </div>

                <div className="field-group">
                  <label>Fabricante</label>
                  <div className="search-box">
                    <Factory size={16} />
                    <input type="text" placeholder="Buscar fabricante..." />
                  </div>
                </div>

                <div className="divider" />

                <div className="field-group">
                  <label>Lote</label>
                  <input type="text" value={drawerItem.batch} className="full-input" />
                </div>

                <div className="field-group">
                  <label>Data de Validade</label>
                  <input type="date" value={drawerItem.expiry} className="full-input" />
                </div>
              </div>
            </div>

            <footer className="drawer-footer">
              <button className="btn-cancel" onClick={() => setDrawerItem(null)}>Cancelar</button>
              <button className="btn-apply" onClick={() => setDrawerItem(null)}>Confirmar Resolução</button>
            </footer>
          </div>
        </>
      )}
    </div>
  );
};

export default DirectInbound;
