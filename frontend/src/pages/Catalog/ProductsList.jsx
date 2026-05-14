import React, { useState } from 'react';
import { 
  Search, 
  Plus, 
  Filter, 
  MoreVertical, 
  Package,
  CheckCircle2,
  AlertCircle,
  Barcode,
  History
} from 'lucide-react';
import './Catalog.css';

const ProductsList = () => {
  const [products, setProducts] = useState([
    { id: '1', name: "DIPIRONA SODICA 500MG/ML", sku: "789456123002", principle: "DIPIRONA SODICA", status: "SYNCED", stock: 1250 },
    { id: '2', name: "AMOXICILINA 500MG", sku: "789123456001", principle: "AMOXICILINA", status: "SYNCED", stock: 450 },
    { id: '3', name: "PARACETAMOL 750MG", sku: "789111222333", principle: "PARACETAMOL", status: "PENDING", stock: 0 },
  ]);

  return (
    <div className="catalog-page">
      <header className="page-header">
        <div>
          <h1>Produtos Acabados</h1>
          <p>Gerenciamento do catálogo completo de itens do almoxarifado.</p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary">
            <Barcode size={18} />
            Gerar Etiquetas
          </button>
          <button className="btn-primary">
            <Plus size={18} />
            Novo Produto
          </button>
        </div>
      </header>

      <div className="filter-bar">
        <div className="search-input">
          <Search size={18} />
          <input type="text" placeholder="Buscar por Nome, SKU ou GTIN..." />
        </div>
        <div className="filter-groups">
          <button className="btn-filter">
            <Filter size={18} />
            Categorias
          </button>
          <button className="btn-filter">
            <History size={18} />
            Últimas Alterações
          </button>
        </div>
      </div>

      <div className="catalog-grid">
        <table className="data-table">
          <thead>
            <tr>
              <th>Produto / SKU</th>
              <th>Princípio Ativo</th>
              <th>Estoque Atual</th>
              <th>Sincronia ERP</th>
              <th className="text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            {products.map(p => (
              <tr key={p.id}>
                <td>
                  <div className="item-name-cell">
                    <Package size={18} className="icon-subtle" />
                    <div>
                      <span className="main-name">{p.name}</span>
                      <span className="sub-name mono">{p.sku}</span>
                    </div>
                  </div>
                </td>
                <td>{p.principle}</td>
                <td>
                  <span className={`stock-count ${p.stock < 100 ? 'low' : ''}`}>
                    {p.stock} un
                  </span>
                </td>
                <td>
                  <div className={`status-badge ${p.status.toLowerCase()}`}>
                    {p.status === 'SYNCED' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
                    {p.status === 'SYNCED' ? 'Integrado' : 'Aguardando Sinc.'}
                  </div>
                </td>
                <td className="text-right">
                  <button className="icon-btn">
                    <MoreVertical size={18} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ProductsList;
