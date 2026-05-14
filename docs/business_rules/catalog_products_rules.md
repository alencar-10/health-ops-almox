# Regras de Negócio: Cadastro de Produtos (Standalone)

Esta tela é responsável pela gestão direta do catálogo de produtos acabados, independente de notas fiscais.

## 1. Regras de Cadastro
* **SKU**: Código único do produto no sistema HealthOps. Geralmente segue um padrão interno ou o código do fabricante.
* **EAN/GTIN**: Código de barras comercial. Deve ser validado (13 dígitos) para garantir unicidade global.
* **Vínculo Obrigatório**: Todo produto acabado deve estar obrigatoriamente vinculado a um **Princípio Ativo** já existente.

## 2. Especificações Técnicas (API)

### Listar Produtos
**URL:** `GET http://localhost:8001/almox/v1/products/`

**cURL Bash:**
```bash
curl -X 'GET' \
  'http://localhost:8001/almox/v1/products/?page=1&limit=20' \
  -H 'accept: application/json'
```

### Criar Novo Produto
**URL:** `POST http://localhost:8001/almox/v1/products/`

**cURL Bash:**
```bash
curl -X 'POST' \
  'http://localhost:8001/almox/v1/products/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "AMOXICILINA 500MG COMPRIMIDO",
  "sku": "AMX-500-REF-01",
  "ean": "7891234567890",
  "unit_of_measure": "UNIT",
  "active_ingredient_id": "1784023b-19ef-4772-af35-bd5e3a051a6f"
}'
```

## 3. Estados de Sincronia
* **LOCAL_ONLY**: Produto cadastrado no HealthOps mas ainda não enviado ao ERP.
* **ERP_SYNCED**: Produto já integrado e com `external_id` (DT_RowId) confirmado no Vivver.
* **FAILED**: Erro na última tentativa de sincronização (ex: SKU duplicado no ERP).
