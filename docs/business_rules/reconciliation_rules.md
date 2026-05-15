# Regras de Negócio: Reconciliação de Nota Fiscal (XML) [BETA]

Esta tela é responsável por vincular itens vindos de um XML de fornecedor com o catálogo interno do ERP Vivver.

## 1. Fluxo Operacional
1. O sistema lê o XML e identifica os itens.
2. A IA (ou lógica fuzzy) sugere um vínculo com base em GTIN, Nome e Fabricante.
3. O operador deve **Validar** ou **Trocar** a sugestão.
4. O item só é considerado "Pronto" após a confirmação humana.

## 2. Critérios de Score (Sugestão IA)
* **Score > 90%**: Considerado "Match Perfeito". O botão aparece azul ("Confirmar Vínculo").
* **Score < 90% ou Divergência Semântica**: O botão aparece amarelo ("Validar e Confirmar"), exigindo atenção redobrada.
* **Divergência Crítica**: Quando a dosagem ou forma farmacêutica não batem, um alerta vermelho é exibido no card.

## 3. Especificações Técnicas (API)

### Endpoint: Registro de Novo Medicamento (Shortcut)
Utilizado quando o produto não existe no Vivver e precisa ser criado "na hora".

**URL:** `POST http://localhost:8000/almox/v1/catalog/register-medicine`

**cURL Bash (Para teste manual):**
```bash
curl -X 'POST' \
  'http://localhost:8000/almox/v1/catalog/register-medicine?tenant_id=fb0282be-1b58-40ce-a124-1cf897e1a393&unit_id=3d14d3ea-52f4-42f7-bfa3-4e1fa1aabd42' \
  -H 'accept: application/json' \
  -H 'x-tenant-id: fb0282be-1b58-40ce-a124-1cf897e1a393' \
  -H 'x-unit-id: 3d14d3ea-52f4-42f7-bfa3-4e1fa1aabd42' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "DIPIRONA SODICA 500MG/ML",
  "sku": "789456123002",
  "form_id": "1",
  "group_id": "01",
  "subgroup_id": "001",
  "uom_id": "1"
}'
```

### Endpoint: Confirmar Vínculo (Reconciliação)
Utilizado para confirmar que o item do XML corresponde a um produto já existente.

**URL:** `PUT http://localhost:8000/almox/v1/inbound/items/{item_id}/reconcile`

**cURL Bash:**
```bash
curl -X 'PUT' \
  'http://localhost:8000/almox/v1/inbound/items/1/reconcile' \
  -H 'accept: application/json' \
  -H 'x-tenant-id: fb0282be-1b58-40ce-a124-1cf897e1a393' \
  -H 'Content-Type: application/json' \
  -d '{
  "product_id": "fb0282be-1b58-40ce-a124-1cf897e1a393",
  "score": 95,
  "metadata": {"match_fields": ["gtin", "name"]}
}'
```

## 4. Tratamento de Erros
* **409 Conflict**: Produto já cadastrado no catálogo (Idempotência).
* **500 Internal Error**: Falha na comunicação com o ERP Vivver ou erro de serialização UUID.
