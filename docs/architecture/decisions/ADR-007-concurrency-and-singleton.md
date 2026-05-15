# ADR-007: Concurrency & Auth Engine Management

## Contexto
Cada instância do Playwright consome recursos significativos. Lançar um novo browser para cada requisição ou permitir que múltiplos contextos mutáveis existam para o mesmo operador gera riscos de concorrência e instabilidade.

## Decisão
Implementar um **Manager de Sessões** (AuthManager) que:
1. Gerencia instâncias de browsers/contextos de forma centralizada.
2. Garante que para um dado Operador + Unidade, exista apenas uma autoridade ativa.
3. Utiliza locks para evitar manobras de switch concorrentes.

## Consequências
- **Prevenção de Drifts**: Evita que duas threads tentem trocar de unidade simultaneamente na mesma sessão do Vivver.
- **Eficiência**: Reutilização de contextos para operações subsequentes (Short-lived cache).
- **Isolamento**: Garante que o contexto operacional de um operador não vaze para outro no mesmo ambiente de execução.
