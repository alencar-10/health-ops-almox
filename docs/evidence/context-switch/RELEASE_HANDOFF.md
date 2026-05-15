# RELEASE HANDOFF — Context Engine v1

**Ciclo:** Context Commit Protocol stabilization  
**Data:** 2026-05-15  
**Recovery point:** tag `context-engine-stable-v1`

---

## 1. Branch final

| Item | Valor |
|------|--------|
| **Branch de release** | `release/context-commit-stable` |
| **Base** | `ca215ab` (Operational/Session context separation + ADRs) |
| **Não mergear ainda** | `main` — aguardar review da PR |
| **Trabalho paralelo** | `feature/platform-core-hardening` (UX, invariants, requirements) |

---

## 2. Commits relevantes (ordem)

| SHA | Mensagem |
|-----|----------|
| `a21b681` | `feat(context-engine): stabilize vivver commit protocol` |
| `021d0dc` | `docs(context): add Core Stabilization PR template and body` |
| `2673630` | `docs(context): add institutional CHANGELOG_CONTEXT_ENGINE` |
| `*` | `chore(release): gitignore, untrack caches, handoff` (após limpeza) |

Tag oficial aponta para **HEAD** da `release/context-commit-stable` após push.

---

## 3. Tag oficial

```bash
git tag -l "context-engine*"
# context-engine-stable-v1
```

**Push da tag (após mover para HEAD):**

```bash
git push origin context-engine-stable-v1 --force
```

---

## 4. Riscos conhecidos

Ver [CHANGELOG_CONTEXT_ENGINE.md](./CHANGELOG_CONTEXT_ENGINE.md) — seção **Known risks**.

Resumo:

- Seletores `#unidade_info` / `#setor_info` podem mudar no Vivver
- Sem context drift monitor
- Soak / stress tests pendentes
- `OperationStore` in-memory
- Python **3.13** obrigatório para Playwright no Windows
- Recovery policy parcial

---

## 5. Subir em outra máquina

```bash
git clone <URL_DO_REPO>
cd health-ops-almoxarifado
git fetch origin
git checkout release/context-commit-stable
# ou: git checkout context-engine-stable-v1

cd backend
py -3.13 -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
playwright install chromium

cd ../frontend
npm install
```

---

## 6. Variáveis obrigatórias

Criar `backend/.env` (nunca commitar):

| Variável | Exemplo / nota |
|----------|----------------|
| `VIVVER_USER` | CPF/conta operador Vivver |
| `VIVVER_PASS` | Senha |
| `VITE_MUNICIPALITY_ID` | `3128253` (Guaraciama) |
| `VIVVER_URL` | `https://guaraciama-mg.vivver.com` |
| `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST`, `DB_PORT` | PostgreSQL |
| `DATABASE_URL` | URL async SQLAlchemy |
| `VIVVER_OPERATOR_ID` | ID Vivver (`codoperador`) — lookups de unidade/setor; ver onboarding |

Frontend `frontend/.env` (PRODUCTION):

```env
VITE_APP_MODE=PRODUCTION
VITE_API_URL=http://127.0.0.1:8000
```

---

## 7. Ordem de boot

**Fonte de verdade:** [OFFICIAL_LOCAL_PORTS.md](../OFFICIAL_LOCAL_PORTS.md) — backend **8000**, frontend **5173**, ordem Backend → Playwright (install + fluxo no processo API) → Frontend.

Resumo:

1. PostgreSQL acessível (se módulos DB forem usados)
2. **Backend** (Python 3.13) na **8000** — hospeda também o **Playwright** usado pelo Vivver. Na **primeira** vez nesta máquina/venv:

```bash
playwright install chromium
```

Depois mantenha o servidor:

```bash
cd backend
py -3.13 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

3. **Frontend** (`npm run dev` na **5173**) — apenas **depois** de `/docs` responder em `127.0.0.1:8000`.

```bash
cd frontend
npm run dev
# UI: http://localhost:5173 — ver docs/OFFICIAL_LOCAL_PORTS.md (host IPv4/IPv6)
```

4. Abrir UI → login implícito via backend → testar troca no TopBar

---

## 8. Comandos de validação

```bash
# API — PSF + ATENDIMENTO (sector 0)
curl -s -m 180 -X POST "http://127.0.0.1:8000/almox/v1/session/switch?unit_id=2&sector_id=0"
curl -s "http://127.0.0.1:8000/almox/v1/session/current"

# API — Almoxarifado
curl -s -m 180 -X POST "http://127.0.0.1:8000/almox/v1/session/switch?unit_id=14&sector_id=10"
curl -s "http://127.0.0.1:8000/almox/v1/session/current"

# Testes unitários
cd backend && py -3.13 -m pytest tests/test_conexao_commit_validation.py -q

# Lab forense (opcional)
py -3.13 -m scripts.lab_context_commit_trace --scenario ujs_click --unit-id 14 --sector-id 10
```

---

## 9. Cenários já validados

| Cenário | Params | Status |
|---------|--------|--------|
| PSF + ATENDIMENTO | `2/0` | COMPLETED (~24s cold, ~5s warm) |
| Almoxarifado | `14/10` | COMPLETED (~20s) |
| Roundtrip | `2/0` ↔ `14/10` | COMPLETED |
| Pré-fix `sector_id=0` | `2/0` | MULTIPLE_CHOICES ~2s (regressão documentada) |

Detalhes: [VALIDATED_SCENARIOS.md](./VALIDATED_SCENARIOS.md)

---

## 10. Troubleshooting inicial

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| `MULTIPLE_CHOICES` em 2s | Setor não enviado / `0` rejeitado (versão antiga) | Confirmar branch `release/*` e `session.py` |
| Overlay travado | Deadlock ou backend 3.14 | Python 3.13; reiniciar uvicorn |
| UI volta ao Almoxarifado | `/current` stale | Confirmar `lastSwitchRef` no frontend da release |
| `NotImplementedError` subprocess | Playwright + Python 3.14 | Usar 3.13 |
| `COMMIT_NOT_SENT` | UJS não disparou | Ver `last_switch_error.html` local; rodar lab trace |
| `ERR_ABORTED` em goto | Redirect pós-commit | `safe_goto_home` na release |
| `REVALIDATION_FAILED` | Manobra exceção | Logs uvicorn + `backend/last_switch_commit.json` |

---

## 11. Arquivos críticos do Context Engine

| Arquivo | Função |
|---------|--------|
| `backend/app/core/auth/adapters/playwright/clients/conexao_commit.py` | POST UJS único |
| `backend/app/core/auth/adapters/playwright/clients/context_switcher.py` | Manobra transacional |
| `backend/app/core/auth/adapters/playwright/adapter.py` | Orquestrador + hidratação |
| `backend/app/core/auth/adapters/playwright/trace/commit_trace.py` | Snapshots, fingerprint, barra |
| `backend/app/api/v1/session.py` | API switch + `_resolve_sector_id` |
| `backend/app/core/auth/operations.py` | State machine |
| `frontend/src/core/context/SessionContext.jsx` | Intenção + anti-stale |

---

## 12. Baseline institucional do ciclo

| Artefato | Path |
|----------|------|
| Protocolo v1 | [COMMIT_PROTOCOL_v1.md](./COMMIT_PROTOCOL_v1.md) |
| Causa raiz | [ROOT_CAUSE_ANALYSIS.md](./ROOT_CAUSE_ANALYSIS.md) |
| Changelog | [CHANGELOG_CONTEXT_ENGINE.md](./CHANGELOG_CONTEXT_ENGINE.md) |
| Evidência xhr ok | `backend/evidence/context-switch/ujs_click_trace.json` |
| Evidência bug duplo POST | `backend/evidence/context-switch/legacy_trace.json` |
| PR body | [PR_CORE_STABILIZATION_BODY.md](./PR_CORE_STABILIZATION_BODY.md) |
| Working tree audit | [WORKING_TREE_AUDIT.md](./WORKING_TREE_AUDIT.md) |

---

## 13. Remote, push e PR (pendente se sem URL)

```bash
git remote add origin <URL_DO_REPO>
git remote -v

git push -u origin release/context-commit-stable
git push origin context-engine-stable-v1 --force

gh pr create --base main --head release/context-commit-stable \
  --title "Stabilize Vivver Context Commit Protocol (v1)" \
  --body-file docs/evidence/context-switch/PR_CORE_STABILIZATION_BODY.md
```

**Não fazer merge imediato** — PR como documentação viva e review institucional.

---

## 14. Contato com o ciclo anterior

- Diagnóstico pré-forense: [CONTEXT_SWITCH_DIAGNOSIS.md](../../../CONTEXT_SWITCH_DIAGNOSIS.md) (arquivado)
- Evolução: [CONTEXT_SWITCH_EVOLUTION.md](./CONTEXT_SWITCH_EVOLUTION.md)

*Handoff gerado para continuidade sem memória implícita.*
