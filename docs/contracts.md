# Contratos Operacionais - Almoxarifado

Este documento define a verdade absoluta sobre as entidades e regras de negócio do sistema. Nenhuma implementação deve divergir destas definições.

## 1. Enums Globais

- **Status (Geral)**: `ACTIVE`, `INACTIVE`, `BLOCKED`
- **MovementType**: `ENTRY` (Entrada), `EXIT` (Saída), `ADJUSTMENT` (Ajuste), `TRANSFER` (Transferência)
- **UnitOfMeasure**: `UNIT`, `BOX`, `BOTTLE`, `AMPOULE`
- **ImportStatus**: `PENDING`, `VALIDATING`, `READY`, `PROCESSING`, `COMPLETED`, `FAILED`, `ABORTED`

## 2. Entidades de Cadastro Mestre (Master Data)

### 2.1. active_ingredients (Princípios Ativos)
- `id`: UUID (PK)
- `name`: VARCHAR (Not Null)
- `description`: TEXT (Optional)
- `status`: Enum ProductStatus (Default: ACTIVE)
- `created_at`: TIMESTAMPTZ
- `updated_at`: TIMESTAMPTZ
- `deleted_at`: TIMESTAMPTZ (Optional)

### 2.2. manufacturers (Fabricantes)
- `id`: UUID (PK)
- `corporate_name`: VARCHAR (Not Null)
- `trade_name`: VARCHAR (Optional)
- `document`: VARCHAR (Normalizado: apenas números)
- `status`: Enum SupplierStatus (Default: ACTIVE)
- `created_at`: TIMESTAMPTZ
- `updated_at`: TIMESTAMPTZ

### 2.3. suppliers (Fornecedores)
- `id`: UUID (PK)
- `corporate_name`: VARCHAR (Not Null)
- `trade_name`: VARCHAR (Optional)
- `document`: VARCHAR (Normalizado: apenas números)
- `contact_name`: VARCHAR (Optional)
- `email`: VARCHAR (Optional)
- `phone`: VARCHAR (Optional)
- `status`: Enum SupplierStatus (Default: ACTIVE)
- `created_at`: TIMESTAMPTZ
- `updated_at`: TIMESTAMPTZ

### 2.4. products (Produtos)
- `id`: UUID (PK)
- `sku`: VARCHAR (Not Null, Unique) - Obrigatório interno
- `ean`: VARCHAR (Optional, Unique) - Código de barras
- `name`: VARCHAR (Not Null)
- `active_ingredient_id`: UUID (FK -> active_ingredients, Optional)
- `manufacturer_id`: UUID (FK -> manufacturers, Optional)
- `unit_of_measure`: Enum UnitOfMeasure (Default: UNIT)
- `stock_current`: DECIMAL (Default: 0) - Cache materializado
- `minimum_stock`: DECIMAL (Default: 0)
- `status`: Enum ProductStatus (Default: ACTIVE)
- `created_at`: TIMESTAMPTZ
- `updated_at`: TIMESTAMPTZ

## 3. Entidades Transacionais (Transactional Data)

### 3.1. inventory_movements (Ledger)
- `id`: UUID (PK)
- `product_id`: UUID (FK -> products, Not Null)
- `movement_type`: Enum MovementType (Not Null)
- `quantity`: DECIMAL (Not Null) - **SEMPRE POSITIVA**
- `reference_document`: VARCHAR (Optional) - Ex: NF, Protocolo
- `supplier_id`: UUID (FK -> suppliers, Optional)
- `notes`: TEXT (Optional)
- `created_by`: VARCHAR (Not Null) - Nome ou Identificador temporário (sem FK por enquanto)
- `created_at`: TIMESTAMPTZ

## 4. Camada de Ingestão (Ingestion Layer)

### 4.1. import_sessions (Sessões de Importação)
- `id`: UUID (PK)
- `type`: VARCHAR (Ex: `XLSX_PRODUCTS`, `XML_NFE`)
- `source_filename`: VARCHAR
- `status`: Enum ImportStatus (Default: PENDING)
- `total_rows`: INTEGER (Default: 0)
- `processed_rows`: INTEGER (Default: 0)
- `success_rows`: INTEGER (Default: 0)
- `error_rows`: INTEGER (Default: 0)
- `is_dry_run`: BOOLEAN (Default: TRUE)
- `started_by`: VARCHAR
- `started_at`: TIMESTAMPTZ
- `finished_at`: TIMESTAMPTZ

## 5. Regras de Integridade e Ingestão

1. **Documentos**: CNPJ/CPF devem ser salvos sem máscara (apenas números).
2. **Quantidades**: O `movement_type` dita a direção. Entrada soma no `stock_current`, Saída subtrai. O valor gravado é sempre positivo.
3. **Atomicidade**: Toda criação de registro em `inventory_movements` deve atualizar o `products.stock_current` na mesma transação.
4. **Imutabilidade**: Registros de `inventory_movements` são imutáveis. Correções via `ADJUSTMENT`.
5. **Ingestão Controlada**: Nenhuma importação em massa pode persistir diretamente sem preview e confirmação explícita.
6. **Fluxo de Ingestão**: Upload -> Parsing -> Preview (Staging) -> Validação -> Dry-run -> Confirmação -> Persistência.
7. **Rastreabilidade**: Toda importação deve gerar uma `import_session`.
8. **Adapters**: O sistema deve usar adaptadores para converter diferentes fontes (XLSX, XML, Manual) em um payload operacional único antes da persistência.
