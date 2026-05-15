# Context Switch — Evidência Forense Institucional

**Marco:** `context-engine-stable-v1`  
**Data:** 15/05/2026

Este diretório preserva a **causalidade técnica** da estabilização da persistência contextual no Vivver (protocolo `create_conexao`).

---

## Leitura obrigatória antes de alterar código

**Aplica-se a humanos e a agentes automatizados (IA).**  

Não altere frontend, backend de sessão/contexto Vivver nem rotas `/almox/v1/session/*` com base apenas em buscas pontuais no repositório. Projetos neste nível já têm invariantes documentados; ignorar esse núcleo gera regressões graves (fluxo ERP, POST duplo, `sector_id`, CSRF).

1. Ler **nesta ordem** ao entrar no tema contexto/Unidade/Setor (primeira leitura = “em que pé” está o projeto):
   1. [README.md](./README.md) *(este documento — tabela + ordem)*  
   2. [CHANGELOG_CONTEXT_ENGINE.md](./CHANGELOG_CONTEXT_ENGINE.md) — visão executiva do que está estável vs. arriscado  
   3. [CONTEXT_SWITCH_EVOLUTION.md](./CONTEXT_SWITCH_EVOLUTION.md) — histórico técnico (tentativas, hipóteses descartadas, estratégia)  
   4. [ROOT_CAUSE_ANALYSIS.md](./ROOT_CAUSE_ANALYSIS.md) — causa raiz (DOM vs ERP, `sector_id=0`, duplo POST, etc.)  
   5. [COMMIT_PROTOCOL_v1.md](./COMMIT_PROTOCOL_v1.md) — contrato soberano com o Vivver (payload, CSRF, failure modes)  
   6. [CONTEXT_COHERENCE_RULES.md](../../core-platform/CONTEXT_COHERENCE_RULES.md) — regras arquiteturais (ânchora Unidade/Setor, lock, soberania ERP) — **local correto:** `docs/core-platform/`, não `docs/architecture/`  
   7. [platform_invariants.md](../../ai-rules/platform_invariants.md) — congelamentos e invariantes globais da plataforma  
   8. *(Quando aplicável ao escopo)* [ARCHITECTURAL_IMPACT.md](./ARCHITECTURAL_IMPACT.md) — o que pode entrar em merge vs. o que fica de fora  

2. Opcionalmente, para baseline operacional (tempos, cenários PSF ↔ Almox): [VALIDATED_SCENARIOS.md](./VALIDATED_SCENARIOS.md) e [LESSONS_LEARNED.md](./LESSONS_LEARNED.md).

**Somente depois disso:** alterações **mínimas**, alinhadas a esses documentos; duvidas → novo ADR/evidência, não “quick fix” incompatível com o protocolo v1.

**Operação local (env, boot):** [RELEASE_HANDOFF.md](./RELEASE_HANDOFF.md).

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
| [RELEASE_HANDOFF.md](./RELEASE_HANDOFF.md) | **Handoff operacional** (boot, env, validação) |
| [FRONTEND_BASELINE_PROTOCOL.md](../../core-platform/FRONTEND_BASELINE_PROTOCOL.md) | **Checklist pré-merge** do shell / TopBar (smoke, hidratação, switch, stale, recovery, tag sugerido) |
| [WORKING_TREE_AUDIT.md](./WORKING_TREE_AUDIT.md) | Auditoria IN/OUT da release |

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

*(Após a [secção de leitura obrigatória](#leitura-obrigatória-antes-de-alterar-código), no topo deste ficheiro.)*

- [CONTEXT_COHERENCE_RULES.md](../../core-platform/CONTEXT_COHERENCE_RULES.md)
- [ADR-004 Context Switching](../../architecture/decisions/ADR-004-context-switching.md)
