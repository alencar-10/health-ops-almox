# Convenções de Desenvolvimento - Almoxarifado

Para garantir a consistência e evitar o "drift" arquitetural durante o desenvolvimento assistido por IA, este projeto seguirá rigorosamente as seguintes convenções:

## 1. Banco de Dados & Modelagem

- **Identificadores (PK)**: Usar `UUID` (v4) para todas as chaves primárias.
- **Naming (Tabelas/Colunas)**: 
    - Tabelas em snake_case e no plural (ex: `products`, `inventory_movements`).
    - Colunas em snake_case.
- **Datas**: Usar `TIMESTAMPTZ` (timestamp with time zone) para todos os campos de data/hora.
- **Exclusão Lógica**: Evitar exclusão física. Usar coluna `status` (enum ou string) ou `is_active` (boolean).
- **Movimentações & Estoque**: 
    - **Ledger (Verdade Absoluta)**: Toda movimentação deve gerar um registro em `inventory_movements`.
    - **Materialização (Cache)**: `products.stock_current` é um cache para performance. 
    - **Sincronia**: O cache deve ser atualizado na mesma transação da movimentação.
- **Transações**: Operações críticas (ex: criar movimento + atualizar estoque) devem ser ATÔMICAS.
- **Enums (Congelados)**:
    - `MovementType`: `ENTRY` (Entrada), `EXIT` (Saída), `ADJUSTMENT` (Ajuste), `TRANSFER` (Transferência).
    - `ProductStatus`: `ACTIVE`, `INACTIVE`, `BLOCKED`.
    - `SupplierStatus`: `ACTIVE`, `INACTIVE`.

## 2. Backend (FastAPI)

- **Assincronismo**: Todo o stack será `async` (FastAPI endpoints, SQLAlchemy 2.0 Async, asyncpg).
- **Estrutura de Pastas**:
    - `app/models/`: Definição de modelos SQLAlchemy.
    - `app/schemas/`: DTOs/Schemas Pydantic (separar In/Out).
    - `app/api/`: Rotas/Endpoints.
    - `app/services/`: Lógica de negócio e persistência.
- **Roteamento**: Todas as rotas da API devem ser prefixadas com `/almox` no `main.py`.
- **Configuração Centralizada**: 
    - Usar `app/core/config.py` com `Pydantic Settings`.
    - Fonte única de leitura do `.env` (Singleton).
    - Proibido `os.getenv` espalhado ou `dotenv` em múltiplos locais.
- **Sessão DB & Engine**:
    - Definir `app/db/session.py` com `AsyncSession`, `async_sessionmaker` e `create_async_engine`.
    - Dependência `get_db` para injeção nos endpoints.
- **Base Declarativa**:
    - Usar `app/db/base.py` com `class Base(DeclarativeBase): pass` para evitar metadatas duplicadas.
- **Healthcheck Real**:
    - O endpoint `/health` deve abrir uma sessão e executar um `SELECT 1` para validar a conexão com o Postgres.
- **Naming de DTOs**: 
    - `ProductCreate`, `ProductUpdate`, `ProductRead`.

## 3. Frontend (React + Vite + shadcn/ui)

- **Linguagem**: TypeScript.
- **Componentes**: Priorizar componentes do `shadcn/ui`.
- **Estado**: React Query (TanStack Query) para gerenciamento de dados do servidor.
- **Estilização**: Tailwind CSS.

## 4. Fluxo de Trabalho (IA)

- **Ciclo Curto**: Um objetivo operacional por vez.
- **Validação**: Cada passo deve ser validado (executado/testado) antes de prosseguir para o próximo.
- **Checkpoints**: Commits frequentes após cada pequena entrega funcional.

## 5. Importação de Dados (XLSX/CSV)

- **Fluxo Obrigatório**: 
    1. **Upload**: Recebimento do arquivo.
    2. **Preview/Parser**: Leitura e exibição dos dados para o usuário.
    3. **Validação**: Verificação de duplicidade, EANs, fornecedores e tipos.
    4. **Persistência**: Gravação final apenas após confirmação e validação total.
