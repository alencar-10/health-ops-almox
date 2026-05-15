## Summary

**Core Stabilization PR** — estabiliza a persistência contextual no Vivver via protocolo institucional `POST create_conexao` (Rails UJS), substituindo automação frágil baseada em submit nativo e heurísticas de UI.

Esta PR **não** é merge da branch `feature/platform-core-hardening` inteira. Contém **apenas** o cherry-pick do núcleo context-engine sobre `ca215ab` (branch `release/context-commit-stable`).

**Marco:** tag `context-engine-stable-v1`

---

## Root cause (causa raiz)

Três causas se confundiam e produziam comportamento “aleatório”:

1. **`sector_id="0"` rejeitado semanticamente** — No Vivver, `codsetor=0` é válido (ex.: PSF → ATENDIMENTO). O HealthOps tratava `"0"` como ausente → `MULTIPLE_CHOICES_REQUIRED` em ~2s **sem** executar Playwright → `/current` permanecia no Almoxarifado → UI parecia “reverter”.

2. **`document.forms[0].submit()` bypassava Rails UJS** — Form `data-remote="true"` exige pipeline xhr com `X-CSRF-Token` e payload completo. O fallback nativo gerava um **segundo POST** incompleto (sem CSRF, sem `commit=Confirmar`), em corrida com o POST correto.

3. **DOM preenchido ≠ sessão ERP persistida** — Select2/hidden na tela de conexão não autorizam contexto; soberania exige POST único + rotação de cookie + barra `#unidade_info` / `#setor_info`.

Documentação: [ROOT_CAUSE_ANALYSIS.md](./docs/evidence/context-switch/ROOT_CAUSE_ANALYSIS.md)

---

## Protocol discovered (protocolo descoberto)

| Item | Valor |
|------|--------|
| Endpoint | `POST /seg/operador/{codoperador}/create_conexao` |
| Transport | XHR (`resource_type: xhr`) |
| CSRF | Header `X-CSRF-Token` ← `<meta name="csrf-token">` |
| Payload | `seg_operador[...]` + **`lookup_key[seg_operador[...]]`** espelhados + `commit=Confirmar` |
| Success | HTTP 200 + body contém **`Conexão ativada com sucesso`** |
| Session | `_vmx_saude_session` rotaciona (`session_fingerprint` before ≠ after) |
| UI bar | `#unidade_info`, `#setor_info` na home |

Contrato formal: [COMMIT_PROTOCOL_v1.md](./docs/evidence/context-switch/COMMIT_PROTOCOL_v1.md)

---

## Why it failed before

| Sintoma | Causa real |
|---------|------------|
| PSF + ATENDIMENTO “não troca” | API falhava em 2s (`sector_id=0`); ERP nunca recebia commit |
| Almoxarifado “às vezes funciona” | Setor `10` ≠ `0`; mascarava bug semântico |
| Intermitência pós-confirmar | Enter disparava UJS **às vezes**; `forms[0].submit()` sempre disparava POST inválido #2 |
| Overlay travado | Deadlock `_browser_lock` + switch longo sem timeout (mitigado em branch feature, fora desta PR) |
| Header `N/A` | Seletores `.unidade_nome` inexistentes; barra real é `#unidade_info` |

---

## Why UJS was mandatory

O formulário Vivver é `data-remote="true"`. O commit **não** é navegação full-page — é **um** XHR com serialização Rails UJS. Sem `page.click(#seg_operador_conexao_btn_submit)` + `wait_for_response(create_conexao)`, não há garantia de request institucional.

`wait_for_load_state` após remote form é **irrelevante** (página não recarrega).

---

## Why `forms.submit()` broke persistence

Evidência empírica reversa:

| Trace | POST count | 2º POST |
|-------|------------|---------|
| [`ujs_click_trace.json`](./backend/evidence/context-switch/ujs_click_trace.json) | **1** xhr, CSRF, `commit=Confirmar` | — |
| [`legacy_trace.json`](./backend/evidence/context-switch/legacy_trace.json) | **2** | document, sem CSRF, sem `commit` |

O segundo POST pode invalidar ou competir com a persistência — explica falhas intermitentes com formulário “correto” na tela.

---

## Why `sector_id=0` is valid

Vivver usa `codsetor=0` como chave real (ATENDIMENTO no PSF, `unit_id=2`). Rejeitar `"0"` como falsy é erro de **semântica de domínio**, não de tipo.

Correção: resolver setor explícito para qualquer string exceto `""` e `AUTO_RESOLVE` — ver `session.py` `_resolve_sector_id`.

---

## Why backend gained contextual sovereignty

- **Frontend** expressa intenção (TopBar); não comita no ERP.
- **Backend** executa manobra transacional, valida POST/fingerprint/barra, retorna `OperationalContext` hidratado.
- **`OperationStore`** expõe state machine (`REQUESTED` → … → `COMPLETED` | `FAILED` | `MULTIPLE_CHOICES_REQUIRED`).
- **Fail-closed:** sem sinal soberano, não publicar contexto como válido.

Regras: [CONTEXT_COHERENCE_RULES.md](./docs/core-platform/CONTEXT_COHERENCE_RULES.md)

---

## Empirical evidence (engineering reverse)

Comparar side-by-side:

- `backend/evidence/context-switch/legacy_trace.json` — reproduz bug histórico
- `backend/evidence/context-switch/ujs_click_trace.json` — referência ouro (1 POST, persistido)

Índice forense: [README.md](./docs/evidence/context-switch/README.md)

---

## Validated scenarios

| Scenario | Params | Result | ~Time |
|----------|--------|--------|-------|
| PSF + ATENDIMENTO | `unit_id=2`, `sector_id=0` | COMPLETED | 24s cold / 5s warm |
| Almoxarifado | `14/10` | COMPLETED | ~20s |
| Roundtrip | 2/0 ↔ 14/10 | COMPLETED | — |
| Pre-fix regression | `2/0` | MULTIPLE_CHOICES ~2s | documented |

Detalhes: [VALIDATED_SCENARIOS.md](./docs/evidence/context-switch/VALIDATED_SCENARIOS.md)

---

## Files in this PR (nucleus only)

**Backend:** `conexao_commit.py`, `context_switcher.py`, `adapter.py`, `commit_trace.py`, `session.py`, `operations.py`, `discovery_client.py`, lab scripts, tests, evidence JSON/HTML

**Docs:** `docs/evidence/context-switch/*` (6 forensic artifacts + protocol v1)

**Frontend (minimal):** `SessionContext.jsx`, `sessionMerge.js`, `TopBar.jsx` — coherence with switch API only

---

## Known remaining risks

Honest limitations — not blockers for this stabilization, but tracked:

- **Header selectors still unstable** — Vivver may change `#unidade_info` / `#setor_info`; monitor via lab probes
- **Long-running soak tests pending** — multi-hour session stability not yet automated
- **Concurrent switch stress tests pending** — single browser lock; no multi-tenant parallel proof
- **Context drift monitor not implemented** — post-switch ERP silent change undetected (roadmap in CONTEXT_COHERENCE_RULES)
- **Recovery policy still partial** — `AUTH_EXPIRED` / `REVALIDATION_FAILED` paths exist; full auto-recovery not complete
- **`OperationStore` in-memory** — lost on process restart; not multi-worker safe yet
- **UX overlay / lock** — experimental pieces remain on `feature/platform-core-hardening`, not in this PR
- **Python 3.13 required** for Playwright on Windows (3.14 → `NotImplementedError`)

---

## Test plan

- [ ] `cd backend && py -3.13 -m pytest tests/test_conexao_commit_validation.py -q`
- [ ] `py -3.13 -m scripts.lab_context_commit_trace --scenario ujs_click --unit-id 14 --sector-id 10`
- [ ] `curl -X POST ".../switch?unit_id=2&sector_id=0"` → `COMPLETED`; `GET /current` → unit 2, sector 0
- [ ] `curl -X POST ".../switch?unit_id=14&sector_id=10"` → `COMPLETED`
- [ ] UI PRODUCTION: PSF → ATENDIMENTO permanece no TopBar após overlay
- [ ] Confirmar que **não** entram arquivos OUT (AppShell overlay, requirements experimentais)

---

## Architectural impact

Transformação: automação visual frágil → **middleware contextual consciente de protocolo**.

Ver: [ARCHITECTURAL_IMPACT.md](./docs/evidence/context-switch/ARCHITECTURAL_IMPACT.md) | [LESSONS_LEARNED.md](./docs/evidence/context-switch/LESSONS_LEARNED.md)

---

## Merge instructions

1. Merge **only** `release/context-commit-stable` (squash ou merge commit — preferir merge commit para preservar cherry-pick message).
2. Tag `context-engine-stable-v1` já aponta para o commit desta branch após push.
3. **Do not** merge `feature/platform-core-hardening` wholesale until UX/observability items are reviewed separately.
