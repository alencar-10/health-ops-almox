# Regras de Negócio: Contexto de Sessão (Unidade e Setor)

Este documento descreve como o sistema HealthOps deve gerenciar a seleção de contexto operacional, garantindo paridade com o Vivver ERP.

## 1. Regras de Hierarquia
*   **Município**: Fixo por prefeitura (Ex: Guaraciama - 3128253). Não deve ser alterável pelo operador comum.
*   **Unidade de Saúde**: O operador deve obrigatoriamente selecionar uma unidade válida. Um operador pode ter acesso a +50 unidades.
*   **Setor**: O setor é **dependente** da unidade. Ao trocar de unidade, a lista de setores deve ser resetada e recarregada.

## 2. Referência Visual (Vivver ERP)

### Seleção de Unidade
![Seleção de Unidade](./images/vivver_unit_selection.png)
*O Vivver utiliza um componente de lookup paginado para listar as unidades vinculadas ao operador.*

### Seleção de Setor
![Seleção de Setor](./images/vivver_sector_selection.png)
*O setor é filtrado automaticamente pelo código da unidade selecionada.*

## 3. Especificações Técnicas (cURL)

### Listar Unidades (v3)
```bash
curl 'https://guaraciama-mg.vivver.com/fwk/lookup_edit_v3?model=Seg::Operador::ConexaoQuery.search.distinct&key=codunidade&name=nomfantasia&where=%2Ccodmunicipio%3D3128253%2Ccodoperador%3D1659' \
  -H 'accept: application/json' \
  -H 'x-requested-with: XMLHttpRequest'
```

### Listar Setores por Unidade
```bash
# Onde codunidade=2 é o filtro dinâmico
curl 'https://guaraciama-mg.vivver.com/fwk/lookup_edit_v3?model=Seg::Operador::ConexaoQuery.search.distinct&key=codsetor&name=nomsetor&where=%2Ccodmunicipio%3D3128253%2Ccodunidade%3D2%2Ccodoperador%3D1659' \
  -H 'accept: application/json' \
  -H 'x-requested-with: XMLHttpRequest'
```

---
*Documentado em 14/05/2026 para fins de integração HealthOps.*
