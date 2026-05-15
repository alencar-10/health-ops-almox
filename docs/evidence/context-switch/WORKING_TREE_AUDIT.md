# Working Tree Audit — `release/context-commit-stable`

**Data:** 2026-05-15  
**Objetivo:** Garantir que apenas o **pacote estabilizado** compõe a release; separar ruído local.

---

## Classificação

### Core estabilizado (IN — já commitado na release)

| Área | Paths |
|------|--------|
| Context Engine | `backend/app/core/auth/adapters/playwright/adapter.py` |
| Commit client | `.../clients/conexao_commit.py` |
| Switcher | `.../clients/context_switcher.py` |
| Discovery | `.../clients/discovery_client.py` |
| Trace | `.../trace/commit_trace.py` |
| Operations | `backend/app/core/auth/operations.py` |
| API | `backend/app/api/v1/session.py` |
| Evidence | `backend/evidence/context-switch/*` |
| Labs / tests | `backend/scripts/lab_context*.py`, `lab_vivver_header*.py`, `tests/test_conexao_commit_validation.py` |
| Docs forenses | `docs/evidence/context-switch/*.md` (exceto este audit pós-limpeza) |
| Coherence | `docs/core-platform/CONTEXT_COHERENCE_RULES.md` |
| Frontend mínimo | `SessionContext.jsx`, `sessionMerge.js`, `TopBar.jsx` (switch API) |

**Commits na release:**

```
a21b681 feat(context-engine): stabilize vivver commit protocol
021d0dc docs(context): add Core Stabilization PR template and body
2673630 docs(context): add institutional CHANGELOG_CONTEXT_ENGINE
+ chore commits (gitignore, audit, handoff) após esta revisão
```

### UX transitória (OUT — não commitar na release)

| Path | Motivo |
|------|--------|
| `frontend/src/core/layout/AppShell.jsx` | Overlay experimental |
| `frontend/src/core/layout/AppShell.css` | Lock overlay transitório |
| `frontend/src/core/layout/TopBar.css` | Ajustes visuais |

**Ação:** `git restore` na release branch.

### Experimentos / evolução paralela (OUT)

| Path | Motivo |
|------|--------|
| `docs/ai-rules/platform_invariants.md` | Em evolução na `feature/platform-core-hardening` |
| `requirements.txt` | Tweaks experimentais não validados no marco v1 |

**Ação:** `git restore` na release branch.

### Arquivos temporários (OUT — nunca versionar)

| Path | Motivo |
|------|--------|
| `backend/last_switch_commit.json` | Runtime debug |
| `backend/last_switch_error.html` | Runtime debug |
| `backend/scratch/` | Scripts ad-hoc |
| `test_out*.log`, `real_test.log` | Logs locais |

**Ação:** `.gitignore` + não adicionar.

### Secrets (OUT — nunca versionar)

| Path | Motivo |
|------|--------|
| `backend/.env` | Credenciais Vivver / DB |
| `frontend/.env` | `VITE_*` locais |
| `.env` (raiz) | Secrets |

**Ação:** `.gitignore` + não adicionar.

### Caches (OUT — nunca versionar)

| Path | Motivo |
|------|--------|
| `**/__pycache__/**` | Artefatos Python — 107 paths estavam trackeados por engano histórico |

**Ação:** `.gitignore` + `git rm --cached` em massa na release.

### README raiz (local)

| Path | Classificação |
|------|----------------|
| `README.md` (untracked) | Manifesto geral do projeto — **não** faz parte do marco context-engine; permanece local ou entra em PR futura de documentação geral |

---

## Resultado esperado

```text
git status
# On branch release/context-commit-stable
# nothing to commit, working tree clean
```

---

## Verificação

```bash
git checkout release/context-commit-stable
git status
git diff ca215ab..HEAD --stat
```

Diff deve listar **apenas** paths da tabela “Core estabilizado” + `.gitignore` + docs de release/handoff.
