# ADR-001: Specialized Auth Engine

## Contexto
O sistema precisa interagir com o Vivver ERP, que não possui uma API pública documentada para terceiros. A autenticação depende da manutenção de uma sessão web complexa (cookies, tokens CSRF).

## Decisão
Implementar uma `AuthEngine` baseada em um motor de automação (Playwright) que simula o comportamento de um operador real. Esta engine é desacoplada dos módulos de negócio.

## Consequências
- **Sessão Efêmera**: A sessão deve ser tratada como estado efêmero e revalidável. Não assumimos persistência eterna.
- **Invalidação Parcial**: O sistema deve detectar e reagir à invalidação parcial de cookies ou tokens sem corromper o estado operacional.
- **Prós**: Permite integração com sistemas legados sem API; captura total do estado da sessão.
- **Contras**: Maior consumo de recursos (browser); sensibilidade a mudanças na UI de login.
- **Trade-off**: Aceitamos a latência do Playwright em troca da capacidade de integração real.
