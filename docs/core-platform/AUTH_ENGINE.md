# Core Platform: Authentication Engine

## 1. Visão Geral
O HealthOps utiliza uma **Authentication Engine** desacoplada para gerenciar a identidade do operador e a validade da sessão junto ao ERP Vivver. A plataforma trata a autenticação como um serviço de infraestrutura, e não como uma regra de negócio de módulo.

## 2. Comportamento Arquitetural
A engine de autenticação é responsável por:
1.  **Identificação do Operador**: Autenticação primária via credenciais.
2.  **Captura de Sessão Operational**: Obtenção de cookies, tokens CSRF e tokens de autenticidade.
3.  **Resolução de Bridge**: O sistema utiliza o motor **Playwright** como bridge técnica para automatizar o fluxo de login em interfaces legadas e extrair o estado da sessão.

## 3. Contratos de Engine
*   **Abstração**: Nenhum módulo de negócio (Almoxarifado, Regulação, etc.) deve possuir conhecimento do mecanismo técnico de login (Playwright).
*   **Contextualização**: O resultado de uma autenticação bem-sucedida deve ser a geração de um `OperationalContext` válido.
*   **Persistência**: A engine deve gerenciar a renovação automática de tokens e o fallback em caso de expiração de sessão.

## 4. Implementação Técnica (Adaptador Playwright)
*   **Mecanismo**: Chromium Headless.
*   **Fluxo**:
    *   Navegação até a URL de contexto do tenant.
    *   Preenchimento automatizado de credenciais.
    *   Gestão de seleção de perfis múltiplos (se aplicável).
    *   Extração de `csrf-token` (meta tags) e `authenticity_token` (formulários).
    *   Sincronização de cookies para uso em clientes HTTP leves (httpx/requests).

## 5. Invariantes de Segurança
*   Credenciais nunca devem vazar para os logs.
*   O motor de automação deve rodar exclusivamente em ambiente de servidor (Backend).
*   O frontend recebe apenas o estado do `OperationalContext` e o identificador de sessão, nunca as credenciais brutas.
