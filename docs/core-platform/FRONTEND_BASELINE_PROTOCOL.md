# FRONTEND_BASELINE_PROTOCOL.md

**Natureza:** baseline operacional obrigatória  
**Âmbito:** shell de aplicação (`AppShell`, `TopBar`), hidratação de sessão Vivver via backend, e invariantes de UX em torno de troca de contexto  
**Motivo:** o frontend deixou de ser “só UI”: integra o **motor operacional** (contexto Unidade/Setor soberano no ERP).

**Leitura obrigatória associada:** ordem em [context-switch README](../evidence/context-switch/README.md), [COMMIT_PROTOCOL_v1](../evidence/context-switch/COMMIT_PROTOCOL_v1.md), [CONTEXT_COHERENCE_RULES](./CONTEXT_COHERENCE_RULES.md), [VALIDATED_SCENARIOS](../evidence/context-switch/VALIDATED_SCENARIOS.md).  
**Boot técnico:** [RELEASE_HANDOFF](../evidence/context-switch/RELEASE_HANDOFF.md).  
**Guia para nova sessão de IA:** [AI_SESSION_START_HERE.md](../AI_SESSION_START_HERE.md).

---

## Legenda de status

| Status | Significado |
|--------|-------------|
| **PASS** | Critério cumprido; evidência indicada (comando, screenshot ou log). |
| **FAIL** | Critério não cumprido; observações obrigatórias (reprodução, stack, env). |
| **PEND** | Ainda não executado nesta execução registada — **não** equivale a PASS. |
| **N/A** | Critério não aplicável ao ambiente atual (declarar porquê nas observações). |

**Screenshots:** guardar em `docs/evidence/baseline-runs/<AAAA-MM-DD>/` e citar caminho na coluna **Evidência**.

---

## Execução registada (evidência operacional)

| Campo | Valor |
|-------|--------|
| **Branch / commit** | `release/context-commit-stable` @ `afc630b` |
| **Data** | 2026-05-15 |
| **Executor** | Cursor Agent (assistido) + _(completar nome humano se aplicável)_ |
| **SO / Node** | Win32 _(completar versão Node com `node -v`)_ |

> **Instrução:** em cada novo ciclo de validação, duplicar a tabela acima ou acrescentar uma linha na §8 com nova data/commit, para manter histórico.

---

## 1. Checklist obrigatório (validação manual antes de merge em `release`)

Marcar **PASS** / **FAIL** / **PEND** / **N/A**. Não fazer merge da hotfix de shell se qualquer item **crítico** (3–9 em ambiente Vivver real) estiver **FAIL** sem incidente documentado.

| # | Critério | Status | Observações | Tempo (s ou mm:ss) | Evidência |
|---|----------|--------|-------------|-------------------|-----------|
| 1 | **Frontend sobe em clone limpo** — `git clone` → checkout branch → `cd frontend` → `npm ci` → `npm run dev`; Vite URL; opc. `npm run build` exit 0 | **PEND** | Nesta sessão **não** se repetiu `git clone` nem `npm ci` em diretório limpo. Subconjunto: `npm run build` em workspace existente — ver §2. | — | _(screenshot terminal clone+ci quando executar)_ |
| 2 | **TopBar hidrata corretamente** — LAB: labels mock; PRODUCTION + backend: `/almox/v1/session/current` | **PEND** | Validar nos dois modos com utilizador humano. | — | _(TopBar LAB + PRODUCTION)_ |
| 3 | **PRODUCTION funciona** — API em `VITE_API_URL`; GET `/current` 200; badges coerentes | **PEND** | Confirmar `VIVVER_OPERATOR_ID` no backend se dropdown de unidades vier vazio com contexto visível. | — | _(DevTools Network + TopBar)_ |
| 4 | **PSF `2/0`** — switch COMPLETED; `/current` `unit.id=2`, `sector.id=0` | **PEND** | Ver [VALIDATED_SCENARIOS](../evidence/context-switch/VALIDATED_SCENARIOS.md). | — | _(curl ou HAR)_ |
| 5 | **Almox `14/10`** — idem | **PEND** | — | — | |
| 6 | **Roundtrip** — `2/0` → `14/10` → `2/0` | **PEND** | — | — | _(timeline anotada)_ |
| 7 | **Overlay não trava** — sem spinner órfão após COMPLETED/FAIL | **PEND** | — | — | |
| 8 | **Refresh não perde contexto** — reload SPA alinha com ERP | **PEND** | Se divergir, etiquetar STALE e documentar. | — | |
| 9 | **Stale `/current` não limpa sessão** — guardas `prev` no cliente | **PEND** | Revisar comportamento em código + teste manual. | — | |

---

## 2. Smoke tests (rápidos)

| Teste | Status | Observações | Tempo | Evidência |
|-------|--------|-------------|-------|-----------|
| Build produção — `cd frontend && npm run build` | **PASS** | Vite build exit 0; módulos transformados 1746; artefactos em `dist/`. | **~2.10** (reportado pelo Vite) + ~7.3 s wall | comando executado nesta sessão |
| Lint — `npm run lint` | **FAIL** | ESLint exit **1**: `no-unused-vars` (ex.: `React` em vários ficheiros); `react-hooks/refs` em `SessionContext.jsx` (atribuição a `.current` durante render); `react-hooks/set-state-in-effect` em `SessionContext.jsx` / `TopBar.jsx`; `react-refresh/only-export-components`; outros em `Sidebar.jsx`, etc. **~33.8 s** wall. | **~34** | terminal / reexecutar `npm run lint` e anexar log em `baseline-runs/` |
| Porta dev — `npm run dev` | **PEND** | — | — | |

---

## 3. Hydration tests (PRODUCTION)

| # | Passo | Status | Observações | Tempo | Evidência |
|---|--------|--------|---------------|-------|-----------|
| H1 | Backend off, `PRODUCTION` | **PEND** | Esperado: erro legível ou badge; recuperação após backend up. | — | |
| H2 | Backend on, credenciais válidas | **PEND** | Session populada; TopBar completa. | — | |
| H3 | HTTP 401/500 | **PEND** | Mensagem derivada de `detail`; app não bloqueada de forma opaca. | — | |

---

## 4. Context switch tests (UI + API)

| Cenário | Parâmetros | Status | Observações | Tempo | Evidência |
|---------|------------|--------|-------------|-------|-----------|
| PSF + ATENDIMENTO | `unit_id=2`, `sector_id=0` | **PEND** | API COMPLETED + UI | — | |
| Almox | `14` / `10` | **PEND** | — | — | |
| Múltiplos setores | — | **PEND** | MULTIPLE_CHOICES / menu SETOR | — | |

Referência: [VALIDATED_SCENARIOS](../evidence/context-switch/VALIDATED_SCENARIOS.md).

---

## 5. Stale tests

| # | Situação | Status | Observações | Evidência |
|---|----------|--------|-------------|-----------|
| S1 | Após switch OK, `/current` ainda antigo | **PEND** | Manter `prev` até convergir | |
| S2 | Re-fetch futuro | **N/A** | _(quando existir política)_ | |

---

## 6. Recovery tests

| # | Situação | Status | Observações | Evidência |
|---|----------|--------|-------------|-----------|
| R1 | Rede instável durante switch | **PEND** | Erro legível; retentativa | |
| R2 | Timeout longo (~2 min) | **PEND** | Alinhar `SWITCH_TIMEOUT_MS` | |
| R3 | LAB ↔ PRODUCTION | **PEND** | Sem crash | |

---

## 7. Marco pós-merge (tag recomendado)

Depois do merge na `release/context-commit-stable` (ou equivalente governado):

- Sugestão de tag: **`frontend-shell-stable-v1`**.  
- Criar tag só em **HEAD** já integrado e **após** o checklist §1 estar verde (ou incidente registado).

```bash
git tag -a frontend-shell-stable-v1 -m "Frontend shell + TopBar baseline (operational motor)"
git push origin frontend-shell-stable-v1
```

---

## 8. Registo histórico

| Data | Release / tag | Executor | §1 sumário (PASS/FAIL/PEND) | Notas |
|------|----------------|----------|-----------------------------|-------|
| 2026-05-15 | `release/context-commit-stable` @ `afc630b` | Cursor Agent | **PEND** (validação Vivver manual não executada nesta sessão) | §2: build PASS; lint FAIL. Ver guia [AI_SESSION_START_HERE.md](../AI_SESSION_START_HERE.md). |
