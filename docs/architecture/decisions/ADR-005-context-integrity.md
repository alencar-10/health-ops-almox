# ADR-005: Context Integrity & Immutability

## Contexto
O risco de "vazamento de contexto" é crítico.

## Decisão
Estabelecer as `CONTEXT_INTEGRITY_RULES`:
1. **Imutabilidade**: O contexto operacional é imutável durante todo o **ciclo operacional ativo** (da intenção ao commit final).
2. **Concorrência**: Nenhum contexto pode ser compartilhado de forma mutável entre sessões ou operadores distintos.
3. **Validação**: Toda operação de persistência deve validar a autoridade operacional contra o estado real do ERP no momento da execução.

## Consequências
- **Garantia**: Rastreabilidade forense de que cada movimento de estoque ocorreu no local e sob o operador corretos.
