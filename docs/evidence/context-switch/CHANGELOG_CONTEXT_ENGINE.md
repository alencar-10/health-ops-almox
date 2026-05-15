# CHANGELOG — Context Engine

**Produto:** HealthOps Platform — Context Engine  
**Marco:** `context-engine-stable-v1`  
**Protocolo:** Context Commit Protocol v1 (`create_conexao`)  
**Data de consolidação:** 2026-05-15  
**Branch de release:** `release/context-commit-stable`  
**Recovery point:** tag `context-engine-stable-v1`

Este changelog é **institucional**: serve humanos, IA, auditoria, regressão e onboarding.  
Complementa a documentação forense em [README.md](./README.md) — não substitui [COMMIT_PROTOCOL_v1.md](./COMMIT_PROTOCOL_v1.md).

---

## [context-engine-stable-v1] — 2026-05-15

Primeira consolidação arquitetural real do motor de contexto: de exploração baseada em UI para **middleware contextual consciente de protocolo ERP**.

### Added

- **UJS commit protocol** — Persistência via único `POST` xhr `*/create_conexao` com `X-CSRF-Token`, `commit=Confirmar` e pares `lookup_key[...]` (contrato em [COMMIT_PROTOCOL_v1.md](./COMMIT_PROTOCOL_v1.md)).
- **`ConexaoCommitClient`** — Disparo e validação do commit (`page.click` + `expect_response`); marcador de sucesso `Conexão ativada com sucesso`; códigos `COMMIT_NOT_SENT`, `COMMIT_REJECTED`, `COMMIT_RESPONSE_INVALID`.
- **Fail-closed persistence validation** — Troca só conclui se POST único + body de sucesso + `session_fingerprint` alterado; senão `SWITCH_NOT_PERSISTED` / falha explícita.
- **Cookie / session rotation validation** — `session_fingerprint` (tail `_vmx_saude_session` + tail CSRF meta) comparado before/after em `build_session_snapshot()`.
- **Commit tracing** — Módulo `commit_trace.py`; lab `lab_context_commit_trace.py`; evidência `ujs_click_trace.json` vs `legacy_trace.json`.
- **Context switch state machine** — `OperationStore` + `OperationStatus` (`REQUESTED` → `SWITCHING` → `VALIDATING` → `COMPLETED` | `FAILED` | `MULTIPLE_CHOICES_REQUIRED`, …).
- **Sovereign bar hydration** — Leitura pós-commit de `#unidade_info` / `#setor_info`; `safe_goto_home()`; `read_desktop_bar_context()`.
- **Forensic documentation pack** — `ROOT_CAUSE_ANALYSIS`, `CONTEXT_SWITCH_EVOLUTION`, `LESSONS_LEARNED`, `VALIDATED_SCENARIOS`, `ARCHITECTURAL_IMPACT`, `PHASE1_FORENSIC_RUNBOOK`.
- **Context Coherence Rules** — [CONTEXT_COHERENCE_RULES.md](../../core-platform/CONTEXT_COHERENCE_RULES.md) ligado ao protocolo v1.
- **Lab & integration scripts** — `lab_context_switch_integration.py`, `lab_vivver_header_probe.py`, `lab_vivver_header_offline.py`.
- **Unit tests** — `tests/test_conexao_commit_validation.py`.
- **Frontend coherence (mínimo)** — `sessionMerge.js`, `lastSwitchRef` anti-stale `/current`, timeout de switch 130s na API de intenção.

### Fixed

- **`sector_id=0` invalidation** — `codsetor=0` (ex.: PSF ATENDIMENTO) tratado como setor explícito; fim de `MULTIPLE_CHOICES_REQUIRED` em ~2s sem manobra.
- **`forms.submit()` double commit** — Removido `document.forms[0].submit()`; eliminado 2º POST `document` sem CSRF (ver `legacy_trace.json`).
- **Stale `lookup_key` synchronization** — `_try_lookup_key()` + `_sync_lookup_keys()` antes do commit; re-seleção de município na manobra.
- **Discovery `where` clause** — `list_sectors` inclui `codmunicipio` no filtro Vivver.
- **Deadlock `_browser_lock`** — Login fora de lock aninhado; manobra sem re-login dentro do lock.
- **Hydration typo** — `self.page` → `self._page` em `_hydrate_context_from_desktop_bar`.
- **`ERR_ABORTED` pós-commit** — `safe_goto_home()` quando Vivver já redireciona para home.
- **Header selectors** — Substituídos seletores inexistentes (`.unidade_nome`) por `#unidade_info` / `#setor_info`.
- **Frontend revert silencioso** — `fetchSession` não sobrescreve unidade recém-trocada nos primeiros 60s pós-switch.

### Changed

- **Contextual sovereignty** — Backend é fonte de verdade pós-switch; frontend expressa intenção, não persiste no ERP.
- **`PlaywrightContextSwitcher`** — Manobra transacional (município → unidade → setor → commit → snapshot); sem heurística “primeiro setor da lista”.
- **API `POST /almox/v1/session/switch`** — Resolução de setor explícita; metadados de operação com snapshots before/after.

### Deprecated

- Submit nativo de formulário `data-remote="true"` como caminho de commit.
- Validação de persistência por substring fixa (`"ALMOXARIFADO" in unit_after`).
- Confiança exclusiva em Select2/DOM da tela `/conexao` como prova de sessão.

### Evidence & recovery

| Artefato | Uso |
|----------|-----|
| `context-engine-stable-v1` (git tag) | Recovery point conhecido |
| `backend/evidence/context-switch/ujs_click_trace.json` | Prova POST correto (1 xhr) |
| `backend/evidence/context-switch/legacy_trace.json` | Prova POST duplo (bug histórico) |
| `docs/evidence/context-switch/` | Causalidade e onboarding |

---

## Known risks (pós-merge)

Riscos **honestos** — não invalidam o marco v1; orientam roadmap.

| Risco | Impacto | Mitigação planejada |
|-------|---------|---------------------|
| **Header selectors unstable** | Vivver alterar `#unidade_info` / `#setor_info` | Lab probe periódico; fallback Discovery |
| **No context drift monitor yet** | ERP muda contexto após validação inicial | Context Integrity Monitor (CONTEXT_COHERENCE_RULES roadmap) |
| **Soak tests pending** | Estabilidade multi-hora não provada | Suite de soak em CI |
| **Concurrent switch stress tests pending** | Um browser lock / processo | Fila de operações ou pool isolado |
| **`OperationStore` in-memory** | Perda de estado em restart / multi-worker | Persistência de operações |
| **Recovery policy partial** | `AUTH_EXPIRED` / revalidação manual | Política formal de recovery |
| **Python 3.13 on Windows** | 3.14 + Playwright → `NotImplementedError` | venv/documentação de runtime |
| **UX overlay experimental** | Fora da release branch | PR separada pós-merge |

---

## For humans

- Onboarding: começar por [README.md](./README.md) → [ROOT_CAUSE_ANALYSIS.md](./ROOT_CAUSE_ANALYSIS.md) → [COMMIT_PROTOCOL_v1.md](./COMMIT_PROTOCOL_v1.md).
- Regressão: [VALIDATED_SCENARIOS.md](./VALIDATED_SCENARIOS.md) + `curl` / lab scripts.
- Merge controlado: [ARCHITECTURAL_IMPACT.md](./ARCHITECTURAL_IMPACT.md) + [PR_CORE_STABILIZATION_BODY.md](./PR_CORE_STABILIZATION_BODY.md).

## For AI / automation

- Contrato normativo: `COMMIT_PROTOCOL_v1.md` (endpoint, payload, failure codes).
- Evidência empírica: comparar sempre `legacy_trace.json` vs `ujs_click_trace.json` antes de propor `form.submit()` ou waits de navegação.
- Invariante: `sector_id` `"0"` é válido; nunca tratar como ausente.

## For audit

- Causalidade: [CONTEXT_SWITCH_EVOLUTION.md](./CONTEXT_SWITCH_EVOLUTION.md) lista hipóteses descartadas.
- Commit dedicado: `feat(context-engine): stabilize vivver commit protocol`.
- Tag: `context-engine-stable-v1`.

---

## Unreleased / roadmap (não fazem parte de v1)

- Context drift heartbeat
- `AWAITING_USER_SELECTION` (negociação de setor na UI)
- `OperationStore` persistente
- ADR-014 formal referenciando protocolo v1
- Stress / soak em CI

---

*Próxima entrada neste changelog: após merge de `release/context-commit-stable` em `main` e qualquer incremento de versão do protocolo (v1.1+).*
