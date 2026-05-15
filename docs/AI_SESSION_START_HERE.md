# Guia inicial para nova sessão de IA (HealthOps Almox)

**Finalidade:** ser o **primeiro ficheiro** que uma IA (ou humano) abre ao entrar no repositório. Resume o estado do trabalho, aponta para a documentação detalhada e define **próximo foco** sem substituir os docs técnicos.

**Última atualização:** 2026-05-15  
**Branch de referência local:** `release/context-commit-stable` (confirmar com `git branch`)

---

## 1. Ordem de leitura recomendada

### Passo A — Orientação de produto e invariantes (15–30 min)

1. **[README.md](../README.md)** na raiz — URLs, estrutura, lista de docs mandatórios.  
2. **[docs/evidence/context-switch/README.md](evidence/context-switch/README.md)** — **obrigatório** antes de mexer em sessão Vivver, TopBar, `/almox/v1/session/*` ou Playwright de contexto.  
3. **[docs/core-platform/CONTEXT_COHERENCE_RULES.md](core-platform/CONTEXT_COHERENCE_RULES.md)** — soberania do contexto Unidade/Setor no ERP.  
4. **[docs/ai-rules/platform_invariants.md](ai-rules/platform_invariants.md)** — congelamentos da plataforma.

### Passo B — Baseline operacional do shell frontend

5. **[docs/core-platform/FRONTEND_BASELINE_PROTOCOL.md](core-platform/FRONTEND_BASELINE_PROTOCOL.md)** — checklist PASS/FAIL/PEND com campos para tempos e evidências (screenshots). **Atualizar este ficheiro após cada validação séria** — não deixar só “funcionou aqui”.

### Passo C — Arranque técnico local

6. **[docs/evidence/context-switch/RELEASE_HANDOFF.md](evidence/context-switch/RELEASE_HANDOFF.md)** — env, boot backend/frontend, credenciais.

### Passo D — Contratos e decisões

7. **[docs/contracts.md](contracts.md)**  
8. **[docs/architecture/ARCHITECTURE_FREEZE_CHECKLIST.md](architecture/ARCHITECTURE_FREEZE_CHECKLIST.md)**  
9. **[docs/conventions.md](conventions.md)**

---

## 2. Mapa rápido “onde está o quê”

| Área | Pastas / ficheiros-chave |
|------|---------------------------|
| Shell + navegação | `frontend/src/core/layout/AppShell.jsx`, `TopBar.jsx`, `Sidebar.jsx`, CSS associados |
| Sessão e catálogo Unidade/Setor | `frontend/src/core/context/SessionContext.jsx` |
| Troca de contexto no ERP | `backend/app/core/auth/adapters/playwright/` (`adapter.py`, `discovery_client.py`, `context_switcher.py`, `conexao_commit.py`) |
| API de sessão | `backend/app/api/v1/session.py` |
| Entrada Direta (UI atual) | `frontend/src/pages/Inbound/DirectInbound.jsx`, `DirectInbound.css` |
| Regra de negócio Entrada Direta | **[docs/business_rules/direct_inbound_rules.md](business_rules/direct_inbound_rules.md)** |
| Contexto de sessão (regras frontend) | `frontend/docs/business_rules/session_context_rules.md` |
| Evidência forense Vivver | `backend/evidence/context-switch/` (ex.: `ujs_click_trace.json`) |

---

## 3. O que já foi feito (resumo para continuidade)

- **Shell da aplicação:** `AppShell` com grelha, overflow compatível com dropdowns, `Sidebar` + `TopBar` integrados.  
- **Sessão PRODUCTION:** hidratação via `/almox/v1/session/current`; tratamento de erros HTTP; fluxo sequencial sessão → catálogo para reduzir condições de corrida sob carga.  
- **TopBar:** estados explícitos (carregar / vazio / erro) nos dropdowns de Unidade e Setor; correções que evitaram **ecrã branco** (ordem de hooks / `busy`), `setSwitchError` exposto pelo contexto, fecho ao clicar fora.  
- **Backend — descoberta Vivver:** lookups `Seg::Operador::ConexaoQuery` passaram a aceitar **`codoperador`** no `where` quando **`VIVVER_OPERATOR_ID`** está definido no `.env` do backend — alinhado à evidência em `ujs_click_trace.json`. Sem este ID, o ERP costuma devolver **lista vazia** de unidades apesar do contexto atual parecer válido na barra.  
- **Documentação institucional:** pasta `docs/evidence/context-switch/` com protocolo de commit, cenários validados, handoff de release; protocolo de baseline frontend em `FRONTEND_BASELINE_PROTOCOL.md`.  
- **Tag local sugerida no protocolo:** `frontend-shell-stable-v1` — confirmar se foi criada/pushed (`git tag`).

*(Para detalhes técnicos e decisões, seguir sempre os docs da pasta context-switch e ADRs referenciados lá.)*

---

## 4. Próximo foco acordado: Entrada Direta

**Estado:** a página **Entrada Direta** já existe no frontend (`DirectInbound`), com fluxo visual e dados em grande parte **mock / protótipo** (ex.: guardar com `alert`, linhas de exemplo na grelha).

**Dono das validações de negócio:** o utilizador do projeto — cruzar com **[direct_inbound_rules.md](business_rules/direct_inbound_rules.md)** e com o comportamento real do Vivver.

**Para a próxima IA:**

1. Não alterar o motor de contexto (§ context-switch) sem ler os invariantes.  
2. Priorizar **fechar lacunas funcionais** da Entrada Direta segundo prioridades que o utilizador definir (ex.: validação ERP linha a linha, importação Excel, commit atómico vs Vivver).  
3. Qualquer novo comportamento que dependa de **Unidade/Setor** deve respeitar o contexto já hidratado pelo TopBar / `SessionContext`.  
4. Registrar progresso em **`FRONTEND_BASELINE_PROTOCOL.md`** quando couber (evidência); para fluxos só de Entrada Direta, pode criar/evoluir um doc em `docs/evidence/` ou complementar `direct_inbound_rules.md` com decisões datadas.

---

## 5. Variáveis de ambiente que mais costumam causar sintomas estranhos

| Variável | Onde | Notas |
|----------|------|--------|
| `VIVVER_OPERATOR_ID` | `backend/.env` | ID numérico Vivver (`codoperador`). Necessário para listagens de unidade/setor nos lookups; sem isto, dropdown pode mostrar “nenhuma unidade” com contexto ainda visível. |
| `VITE_APP_MODE` | `frontend/.env` | `LAB` vs `PRODUCTION` — define se há chamadas reais ao backend de sessão. |
| `VITE_API_URL` | `frontend/.env` | Base URL da API em modo PRODUCTION. |

---

## 6. Como deixar rasto para a sessão seguinte

1. Atualizar **[FRONTEND_BASELINE_PROTOCOL.md](core-platform/FRONTEND_BASELINE_PROTOCOL.md)** com **Status**, **Observações**, **Tempo**, **Evidência** (screenshot ou caminho).  
2. Guardar imagens em **`docs/evidence/baseline-runs/<AAAA-MM-DD>/`** (criar pasta por dia ou por release).  
3. Se mudou comportamento crítico de contexto, adicionar nota curta em **`docs/evidence/context-switch/CHANGELOG_CONTEXT_ENGINE.md`** ou evidência nova, conforme governança já usada no projeto.

---

## 7. Comandos úteis (smoke rápido)

```bash
# Frontend
cd frontend && npm ci && npm run build && npm run dev

# Backend (ajustar conforme RELEASE_HANDOFF)
cd backend && uvicorn ...
```

Lint: `npm run lint` no frontend — na última execução registada no protocolo **falhou** (ESLint); política do projeto pode ser corrigir só se bloquear CI — ver observações no protocolo.

---

*Este guia não substitui ADRs nem o pacote forense do context-switch; apenas encaminha para lá.*
