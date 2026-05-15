# Platform Baseline: Cycle 31 Stable State

Este documento define o estado "congelado" da plataforma HealthOps após a institucionalização do Core Platform.

## 1. Versões de Contrato
- **Auth Engine**: `v1.2.0` (Session/Context separation)
- **Operational Context**: `v2.0.0` (Strict Domain Separation)
- **Discovery Engine**: `v1.1.0` (Observed Protocol aware)

## 2. Invariantes de Infraestrutura
- **Database**: Postgres 16 (Local isolation on port 5434)
- **ERP Integration**: Vivver Cloud (Guaraciama-MG)
- **Authentication**: Playwright (Headless Chromium)
- **Session Rules**: Ephemeral state, revalidable, transactional rollback.

## 3. Marcos de Estabilidade
- [x] Login real via automação
- [x] Descoberta dinâmica de escopo (Unidades/Setores)
- [x] Manobra de troca de contexto transacional
- [x] Imutabilidade do contexto operacional por requisição
- [x] Rastreabilidade forense de tokens (CSRF/Session)

## 4. Próximos Passos (Aprovados)
1. Integração read-only da TopBar com o `OperationalContext`.
2. Vertical Slice de propagação contextual na UI.
3. Migração gradual dos módulos legados para o novo contrato de Auth.
