# Context Coherence Rules

Este documento estabelece as regras de integridade para a sincronização de contexto entre o HealthOps e o ERP Vivver.

## Fundamentos

1. **ERP Sovereignty**: O Vivver é a fonte da verdade sobre a validade de uma combinação Unidade + Setor.
2. **Atomic Context**: O contexto operacional é uma unidade atômica. Trocas parciais são estados de erro.
3. **Operational Lock**: Bloqueio de mutações enquanto o estado for `SWITCHING`.
4. **Context Negotiation**: Ambiguidades legítimas (múltiplos setores) devem ser tratadas como estados de negociação, não falhas técnicas.

## Taxonomia de Erros e Severidade

| Código | Severidade | Significado | Ação |
| :--- | :--- | :--- | :--- |
| `STALE_CONTEXT` | CRÍTICA | UI divergiu do estado interno do ERP. | Refresh forçado / Lock. |
| `REVALIDATION_FAILED` | CRÍTICA | Falha na validação pós-switch. | Marcar sessão como inconsistente. |
| `INVALID_COMBINATION` | ALTA | ERP rejeitou explicitamente a combinação. | Rollback. |
| `HYDRATION_FAILED` | MÉDIA | Setores não carregaram (AJAX timeout). | Retry. |
| `AUTH_EXPIRED` | MÉDIA | Sessão expirou durante a manobra. | Login. |
| `MULTIPLE_CHOICES` | BAIXA | Resolução ambígua (Negociação pendente). | Exigir escolha humana. |

## Norte Arquitetural (Future Roadmap)

Estas são as diretrizes para evolução do sistema, tratando riscos identificados:

### 1. Context Negotiation State
Substituir o erro `MULTIPLE_CHOICES_REQUIRED` por um estado `AWAITING_USER_SELECTION` no lifecycle da operação, permitindo que a UI apresente as opções válidas retornadas pelo Backend.

### 2. Lock Granular
Evoluir do "Hard Lock" (bloqueio total) para um modelo granular:
- **Hard Lock**: Ações sensíveis a contexto (prescrições, estoque).
- **Soft Lock**: Dashboards e visualizações globais.

### 3. Context Integrity Monitor (Heartbeat)
Implementar um monitor contínuo que valida o contexto em background periodicamente, detectando **Context Drift** (quando o ERP muda o estado silenciosamente após a validação inicial).

### 4. Correlation Lineage
Adicionar `correlation_id` e `context_version` em cada manobra para rastrear tentativas, retries e rollbacks em uma linhagem auditável.

## Context Commit Protocol (v1)

Contrato forense e operacional da persistência no Vivver: [COMMIT_PROTOCOL_v1.md](../evidence/context-switch/COMMIT_PROTOCOL_v1.md).

## Protocolo de Revalidação Atual (P1)

Para esta fase, a revalidação foca em:
- **Snapshot Comparativo**: Antes vs Depois (Unidade/Setor).
- **DOM Evidence**: Nomes reais no cabeçalho.
- **CSRF Refresh**: Garantia de que o token de segurança está operacional.
- **Contextual Endpoint**: Teste de chamada mínima ao Vivver para confirmar autoridade.
