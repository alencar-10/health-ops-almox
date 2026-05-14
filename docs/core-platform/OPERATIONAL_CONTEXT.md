# Core Platform: Operational Context

## 1. Definição
O **Operational Context** é o estado obrigatório e imutável que define a validade de qualquer operação dentro da plataforma HealthOps. Ele resolve a identidade situacional do operador no momento da ação.

## 2. Estrutura do Contexto
Todo módulo da plataforma deve consumir o contexto resolvido, que contém:
*   **Tenant**: Identificador do cliente/prefeitura (ex: Guaraciama - 3128253).
*   **Unidade**: A Unidade de Saúde ativa na sessão (ex: Almoxarifado Central).
*   **Setor**: O setor operacional específico (ex: Atendimento, Sala de Vacina).
*   **Operador**: Identificação e nível de permissão do usuário logado.
*   **Mode**: Estado do ambiente (LAB vs PRODUCTION).

## 3. Regras de Propagação
*   **Injeção Global**: O contexto deve ser injetado no topo da hierarquia da aplicação (SessionProvider no Frontend / Context Middleware no Backend).
*   **Obrigatoriedade**: Nenhuma transação de escrita deve ser processada sem um `OperationalContext` válido e autenticado.
*   **Isolamento**: O contexto garante que um operador nunca execute ações em unidades ou setores para os quais não possui permissão resolvida na sessão.

## 4. Consumo por Módulos
Módulos como Almoxarifado, Regulação ou Auditoria são **consumidores passivos** do contexto.
*   **ERRADO**: O módulo de Almoxarifado pede para o usuário selecionar a unidade.
*   **CERTO**: O módulo de Almoxarifado pergunta à Plataforma: "Em qual unidade o operador está agora?" e utiliza essa informação para filtrar dados.

## 5. Fluxo de Resolução
1.  **Auth Engine** realiza o login.
2.  **Context Resolver** busca no Vivver as unidades e setores permitidos.
3.  **User** seleciona o contexto ativo (Unidade/Setor).
4.  **Plataforma** congela este contexto no `OperationalContext` global.
