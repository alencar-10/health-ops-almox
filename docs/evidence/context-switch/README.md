# Context Switch — Evidência Forense Institucional

**Marco:** `context-engine-stable-v1`  
**Data:** 15/05/2026

Este diretório preserva a **causalidade técnica** da estabilização da persistência contextual no Vivver (protocolo `create_conexao`).

---

## Documentos principais

| Documento | Conteúdo |
|-----------|----------|
| [ROOT_CAUSE_ANALYSIS.md](./ROOT_CAUSE_ANALYSIS.md) | Causa raiz, setor `0`, UI vs commit |
| [CONTEXT_SWITCH_EVOLUTION.md](./CONTEXT_SWITCH_EVOLUTION.md) | Timeline, hipóteses descartadas |
| [COMMIT_PROTOCOL_v1.md](./COMMIT_PROTOCOL_v1.md) | **Contrato v1** (endpoint, payload, CSRF, failure modes) |
| [LESSONS_LEARNED.md](./LESSONS_LEARNED.md) | Lições institucionais |
| [VALIDATED_SCENARIOS.md](./VALIDATED_SCENARIOS.md) | Cenários e tempos observados |
| [ARCHITECTURAL_IMPACT.md](./ARCHITECTURAL_IMPACT.md) | Impacto no HealthOps, merge scope |
| [CHANGELOG_CONTEXT_ENGINE.md](./CHANGELOG_CONTEXT_ENGINE.md) | **Changelog institucional** (Added / Fixed / Known risks) |

## Documentos de suporte

| Documento | Conteúdo |
|-----------|----------|
| [COMMIT_PROTOCOL.md](./COMMIT_PROTOCOL.md) | Fase 1 forense (histórico) |
| [PHASE1_FORENSIC_RUNBOOK.md](./PHASE1_FORENSIC_RUNBOOK.md) | Runbook de captura de traces |

## Evidência runtime

| Artefato | Descrição |
|----------|-----------|
| [`backend/evidence/context-switch/ujs_click_trace.json`](../../../backend/evidence/context-switch/ujs_click_trace.json) | POST único correto (referência) |
| [`backend/evidence/context-switch/legacy_trace.json`](../../../backend/evidence/context-switch/legacy_trace.json) | POST duplo (bug histórico) |
| [`backend/evidence/context-switch/vivver_home_after_login.html`](../../../backend/evidence/context-switch/vivver_home_after_login.html) | DOM da barra `#unidade_info` |

## Código de referência

- [`conexao_commit.py`](../../../backend/app/core/auth/adapters/playwright/clients/conexao_commit.py)
- [`context_switcher.py`](../../../backend/app/core/auth/adapters/playwright/clients/context_switcher.py)
- [`session.py`](../../../backend/app/api/v1/session.py)

## Regras de plataforma

- [CONTEXT_COHERENCE_RULES.md](../../core-platform/CONTEXT_COHERENCE_RULES.md)
- [ADR-004 Context Switching](../../architecture/decisions/ADR-004-context-switching.md)
