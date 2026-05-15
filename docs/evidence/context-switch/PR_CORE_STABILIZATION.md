# PR: Stabilize Vivver Context Commit Protocol (v1)

**Tipo:** Core Stabilization PR (não feature PR)  
**Branch:** `release/context-commit-stable` → `main` (ou `master`)  
**Base commit:** `ca215ab` + cherry-pick `feat(context-engine): stabilize vivver commit protocol`  
**Tag:** `context-engine-stable-v1`

---

## Como abrir esta PR

```bash
# Na máquina com remote configurado
git fetch origin
git checkout release/context-commit-stable
git push -u origin release/context-commit-stable
git push origin context-engine-stable-v1

# GitHub CLI
gh pr create \
  --base main \
  --head release/context-commit-stable \
  --title "Stabilize Vivver Context Commit Protocol (v1)" \
  --body-file docs/evidence/context-switch/PR_CORE_STABILIZATION_BODY.md
```

Se não houver `main`, ajuste `--base` para o branch trunk do repositório.

---

## Escopo IN / OUT

### IN (esta PR)

- Context Engine (`PlaywrightAuthAdapter`, `PlaywrightContextSwitcher`)
- `ConexaoCommitClient` + commit tracing (`commit_trace.py`)
- Context Commit Protocol v1 (documentação forense)
- State machine (`OperationStore` / `OperationStatus`)
- Sector resolution (`sector_id=0` explícito)
- Context Coherence Rules
- Runtime evidence (`legacy_trace.json` vs `ujs_click_trace.json`)
- Validated scenarios + lab scripts
- Fail-closed persistence validation (fingerprint, POST único, barra ERP)
- Coerência mínima frontend: `SessionContext`, `sessionMerge`, `TopBar` (switch API)

### OUT (ficam na branch `feature/platform-core-hardening`)

- Overlays temporários (`AppShell` lock-overlay experimental)
- Freezes / CSS transitório (`TopBar.css`, `AppShell.css`)
- `requirements.txt` experimental
- `docs/ai-rules/platform_invariants.md` em evolução
- Caches `__pycache__`, `.env`, `last_switch_*.html` runtime

---

## Corpo da PR

O texto completo para colar no GitHub está em:

**[PR_CORE_STABILIZATION_BODY.md](./PR_CORE_STABILIZATION_BODY.md)**
