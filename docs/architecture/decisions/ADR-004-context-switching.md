# ADR-004: Transactional Context Switching

## Contexto
Trocar de contexto operacional no Vivver exige sincronização entre UI e tokens de sessão.

## Decisão
Implementar a manobra de troca de contexto como um fluxo transacional com **validação integral e rollback formal**:
1. Navegação UI para a tela de conexão.
2. Seleção de Unidade/Setor via automação.
3. **Re-bootstrap** obrigatório da sessão (novo CSRF e cookies).
4. **Validação Final**: A troca só é considerada concluída após a verificação de que o novo estado está refletido no ERP.

## Regras de Falha
- **Rollback/Invalidação**: Falhas intermediárias (ex: switch parcial) invalidam o contexto atual e exigem retorno ao estado anterior ou reautenticação forçada.
- **Prós**: Evita erros de "422 Unprocessable Entity" após a troca.
- **Contras**: Latência adicional no switch.
