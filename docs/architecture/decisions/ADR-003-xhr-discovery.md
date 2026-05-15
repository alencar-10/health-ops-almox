# ADR-003: XHR-Based Access Scope Discovery

## Contexto
Para listar Unidades e Setores, o sistema intercepta requisições XHR (`lookup_edit_v3`).

## Decisão
Utilizar a interceptação de requisições XHR via Playwright, mas tratando os endpoints como **protocolos observados** e não como APIs oficiais.

## Consequências
- **Protocolo Observado**: A expectativa de estabilidade é baixa; não tratamos como API confiável.
- **Versionamento de Payload**: O sistema deve versionar o parsing do payload observado para detectar mudanças silenciosas do ERP.
- **Prós**: Maior resiliência a mudanças visuais; extração de dados limpos (JSON).
- **Contras**: Dependência de endpoints internos do ERP; necessidade de emular parâmetros de query específicos.
