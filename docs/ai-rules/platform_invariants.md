# Core Platform: Invariantes e Regras de Integridade (AI Rules)

## 1. Regras Absolutas de Arquitetura
Estas regras são imutáveis e devem ser respeitadas em qualquer refatoração ou criação de novas features.

*   **CONTEXTO OBRIGATÓRIO**: O `OperationalContext` é a única fonte de verdade para Tenant, Unidade e Setor. Nunca hardcodar ou redefinir estes valores dentro de módulos.
*   **DESACOPLAMENTO DE AUTH**: Módulos não implementam autenticação. Eles apenas consomem a sessão resolvida pela **Auth Engine**.
*   **PLAYWRIGHT É DETALHE**: O uso de Playwright é um detalhe de implementação infraestrutural. Ele nunca deve vazar para a lógica de negócio dos módulos.
*   **SHELL IMUTÁVEL**: O `AppShell`, `TopBar` e `Sidebar` pertencem à Plataforma (Core). Mudanças nestes componentes devem ser aprovadas via Checklist de Estabilidade.

## 2. Invariantes de Módulo
*   **REUSABILIDADE**: Todo módulo (Almoxarifado, Regulação, etc.) deve ser agnóstico ao cliente. Ele deve funcionar apenas recebendo o `OperationalContext`.
*   **PROPS E CONTRATOS**: Nunca renomear props de contexto existentes. A retrocompatibilidade é prioridade.
*   **ISOLAMENTO DE ESTADO**: O estado de um módulo não deve interferir no estado global de sessão da plataforma.

## 3. Checklist de Integridade (Pré-Merge)
Antes de qualquer alteração ser considerada concluída pela IA:
1.  [ ] O `AppShell` permanece intacto?
2.  [ ] O `OperationalContext` está sendo respeitado?
3.  [ ] Não houve duplicação de lógica de autenticação?
4.  [ ] O mecanismo de bridge (Playwright) continua isolado no Core?
5.  [ ] A página de feature consome os dados via hooks da plataforma (ex: `useSession`)?

## 4. Filosofia de Desenvolvimento
*   **Estabilidade > Velocidade**.
*   **Contratos > Implementação**.
*   **Plataforma > Feature**.
