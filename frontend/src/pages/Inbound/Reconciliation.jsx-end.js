            {/* COLUMN 3: ACTIONS */}
            <div className="col-actions">
              <div className="action-stack">
                {!item.is_confirmed ? (
                  <>
                    <button 
                      className={`btn-action confirm ${item.suggestion.score < 90 || item.suggestion.warnings.length > 0 ? 'warning-friction' : ''}`}
                    >
                      <CheckCircle size={18} />
                      {item.suggestion.score < 90 || item.suggestion.warnings.length > 0 ? 'Validar e Confirmar' : 'Confirmar Vínculo'}
                    </button>
                    
                    <div className="secondary-actions">
                      <button className="btn-action change">
                        <Search size={18} />
                        Trocar
                      </button>
                      <button className="btn-action create" onClick={() => setRegisteringItem(item)}>
                        <PlusCircle size={18} />
                        Cadastrar no Vivver
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="confirmed-status">
                    <CheckCircle size={18} color="var(--success)" />
                    <span>Vinculado</span>
                    <button className="btn-undo" title="Desfazer Vínculo">
                      <ArrowLeftRight size={14} />
                      Desfazer
                    </button>
                  </div>
                )}
              </div>
              <button className="btn-more">
                <MoreVertical size={20} />
              </button>
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
