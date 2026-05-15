# ADR-006: Structural Isolation of the Playwright Adapter

## Contexto
O adaptador Playwright é uma peça de infraestrutura volátil.

## Decisão
Fragmentar o `PlaywrightAuthAdapter` em sub-clientes especializados (`SessionManager`, `DiscoveryClient`, `ContextSwitcher`).

## Consequências
- **Limites de Responsabilidade**: Sub-clientes especializados são puramente agentes de infraestrutura e **não podem conter regras de negócio operacional** ou lógica de decisão de fallback.
- **Prós**: Código mais limpo, fácil de debugar e extensível.
- **Contras**: Maior número de arquivos e classes.
