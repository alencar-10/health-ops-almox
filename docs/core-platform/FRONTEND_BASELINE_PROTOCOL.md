# FRONTEND_BASELINE_PROTOCOL.md

**Natureza:** baseline operacional obrigatória  
**Âmbito:** shell de aplicação (`AppShell`, `TopBar`), hidratação de sessão Vivver via backend, e invariantes de UX em torno de troca de contexto  
**Motivo:** o frontend deixou de ser “só UI”: integra o **motor operacional** (contexto Unidade/Setor soberano no ERP).

**Leitura obrigatória associada:** ordem em [context-switch README](../evidence/context-switch/README.md), [COMMIT_PROTOCOL_v1](../evidence/context-switch/COMMIT_PROTOCOL_v1.md), [CONTEXT_COHERENCE_RULES](./CONTEXT_COHERENCE_RULES.md), [VALIDATED_SCENARIOS](../evidence/context-switch/VALIDATED_SCENARIOS.md).  
**Boot técnico:** [RELEASE_HANDOFF](../evidence/context-switch/RELEASE_HANDOFF.md).

---

## 1. Checklist obrigatório (validação manual antes de merge em `release`)

Marcar **PASS** / **FAIL** / **N/A** na coluna do release. Não fazer merge da hotfix de shell se qualquer item PASS dependente de Vivver falhar sem justificativa registrada (incidente / env).

| # | Critério | PASS = |
|---|----------|--------|
| 1 | **Frontend sobe em clone limpo** | `git clone` → `checkout` da branch candidata → `cd frontend` → `npm ci` (ou `npm install`) → `npm run dev`; Vite imprime URL; sem erro fatal no terminal. Opcional: `npm run build` com exit 0. |
| 2 | **TopBar hidrata corretamente** | Com `VITE_APP_MODE=LAB`: Prefeitura, Unidade e Setor aparecem com labels coerentes (mock). Com `PRODUCTION` e backend OK: mesmo bloco preenchido a partir de `/almox/v1/session/current`. |
| 3 | **`PRODUCTION` funciona** | Backend em `VITE_API_URL`; `GET /almox/v1/session/current` 200 com `data`; TopBar não permanece indefinidamente no estado degradado; badges de modo/erro coerentes. |
| 4 | **PSF `2/0` funciona** | `unit_id=2`, `sector_id=0` (ATENDIMENTO). `POST .../switch` → `COMPLETED`; `GET /current` com `unit.id=2`, `sector.id=0`. Ver referência em [VALIDATED_SCENARIOS](../evidence/context-switch/VALIDATED_SCENARIOS.md). |
| 5 | **Almox `14/10` funciona** | `unit_id=14`, `sector_id=10`. Switch `COMPLETED`; `/current` corresponde. |
| 6 | **Roundtrip funciona** | Sequência mínima: `2/0` → `14/10` → `2/0` novamente; todos os passos `COMPLETED` (tempos variam cold/warm). |
| 7 | **Overlay não trava** | Durante `switch`, indicador de operação em curso; ao `COMPLETED` ou falha terminal, overlay/estado deixa de bloquear cliques de forma órfã; sem spinner infinito. |
| 8 | **Refresh não perde contexto** | Após troca válida, reload da página SPA: `PRODUCTION` deve re-hidratar via `/current` para a mesma combinação esperada (ERP como fonte da verdade — se divergir, documentar sob `STALE_CONTEXT`). |
| 9 | **Stale `/current` não limpa sessão** | Se já existe sessão otimista (`prev`) e `/current` diverge dentro da janela pós-switch documentada no código, UI **não** deve regredir para “sem contexto” apenas por snapshot atrasado — manter `prev` até convergir ou falha explícita. |

---

## 2. Smoke tests (rápidos)

| Teste | Comando / ação | Esperado |
|--------|----------------|----------|
| Build produção | `cd frontend && npm run build` | Exit 0, artefactos em `dist/`. |
| Lint (se política do repo exigir) | `npm run lint` | Política atual: corrigir apenas se bloquear CI. |
| Porta dev | `npm run dev` | URL local anunciada; sem crash. Se 5173 ocupada, Vite escolhe porta seguinte — usar a URL impressa. |

---

## 3. Hydration tests (PRODUCTION)

| # | Passo | Esperado |
|---|--------|----------|
| H1 | Backend off, `PRODUCTION` | Mensagem de erro de ligação ou badge de falha; recuperação após subir backend (`refreshSession` / reload). |
| H2 | Backend on, credenciais válidas | `session` populada; TopBar com três contextos + utilizador. |
| H3 | Resposta HTTP de erro (401/500) | Mensagem derivada de `detail` / status, sem trancar a app inteira de forma opaca. |

---

## 4. Context switch tests (UI + API)

Executar em paralelo observação da API (curl ou DevTools) e do TopBar/dropdowns.

| Cenário | Parâmetros | Verificação API | Verificação UI |
|---------|------------|-----------------|----------------|
| PSF + ATENDIMENTO | `unit_id=2`, `sector_id=0` | `COMPLETED`; `/current` consistente | Dropdowns e labels após conclusão |
| Almox | `14` / `10` | idem | idem |
| Múltiplos setores | Unidade com >1 setor | `MULTIPLE_CHOICES_REQUIRED` se aplicável | Menu SETOR permite escolha; sem `setSwitchError` indefinido |

Referência de comandos: [VALIDATED_SCENARIOS](../evidence/context-switch/VALIDATED_SCENARIOS.md).

---

## 5. Stale tests

| # | Situação | Esperado |
|---|----------|----------|
| S1 | Imediatamente após `switch` bem-sucedido, `/current` ainda devolve unidade antiga | Sessão já preenchida (**`prev`**) não é apagada até convergência ou nova política explicitada em ADR. |
| S2 | Re-fetch periódico (se implementado no futuro) | Nunca sobrescrever combinação validada pelo ERP sem revalidação; ver [CONTEXT_COHERENCE_RULES](./CONTEXT_COHERENCE_RULES.md). |

---

## 6. Recovery tests

| # | Situação | Esperado |
|---|----------|----------|
| R1 | Queda intermitente de rede durante `switch` | Erro utilizador legível; `cancel`/limpeza operação se existir; retentativa possível sem reload obrigatório. |
| R2 | Timeout longo (~2 min) | Mensagem de timeout documentada na UI (alinhamento com `SWITCH_TIMEOUT_MS`). |
| R3 | Alternância LAB ↔ PRODUCTION (badge TopBar) | Sem crash; modo LAB funciona offline relativo ao ERP; modo PRODUCTION volta a hidratar. |

---

## 7. Marco pós-merge (tag recomendado)

Depois do merge na `release/context-commit-stable` (ou equivalente governado):

- Sugestão de tag: **`frontend-shell-stable-v1`** (marca explícito o pacto shell + TopBar + hidratação).  
  Alternativa coordenada com outras linhas da plataforma: **`platform-baseline-v2`** (se já existirem convenções de numeração inter-equipas).

Criar tag só em **HEAD** já integrado e **após** o checklist §1 estar verde (ou registrado incidente).

```bash
git tag -a frontend-shell-stable-v1 -m "Frontend shell + TopBar baseline (operational motor)"
git push origin frontend-shell-stable-v1
```

---

## 8. Registo

| Data | Release / tag | Executor | §1 resultado (sumário) |
|------|----------------|----------|-------------------------|
| _(preencher)_ | _(preencher)_ | _(preencher)_ | _(preencher)_ |
