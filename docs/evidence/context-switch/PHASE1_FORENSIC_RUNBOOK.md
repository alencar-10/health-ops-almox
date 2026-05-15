# Fase 1 — Runbook de Forense de Protocolo (`create_conexao`)

**Objetivo:** Provar qual request comita o contexto no Vivver **antes** de alterar `context_switcher.py`.  
**Proibido nesta fase:** retries, sleeps mágicos, novos waits no switcher, heurísticas de setor.

---

## 1. Entregáveis

| Artefato | Caminho |
|----------|---------|
| Trace JSON (por cenário) | `backend/evidence/context-switch/{scenario}_trace.json` |
| Playwright trace (opcional) | `backend/evidence/context-switch/{scenario}.zip` |
| Relatório consolidado | Atualizar seção 5 de [COMMIT_PROTOCOL.md](./COMMIT_PROTOCOL.md) |
| Timeline correlacionada | Dentro de cada `*_trace.json` → chave `timeline` |

---

## 2. Estrutura do JSON de evidência

```json
{
  "scenario": "legacy | ujs_click | manual",
  "target": { "municipality_id": "3128253", "unit_id": "14", "sector_id": "10" },
  "before": {
    "session": { "cookies": {}, "session_fingerprint": "..." },
    "form": { "hidden_fields": {}, "csrf_meta": "...", "select2_labels": {} },
    "header": { "municipio": "", "unidade": "", "setor": "" }
  },
  "after": { "...": "idem" },
  "commit_verdict": "COMMIT_NOT_SENT | COMMIT_REJECTED | SWITCH_NOT_PERSISTED | PERSISTED",
  "summary": { "create_conexao_post_count": 0 },
  "timeline": [
    { "ts": "...", "event": "navigate_conexao", "url": "..." },
    { "ts": "...", "event": "form_snapshot_pre_commit" },
    { "ts": "...", "event": "http_request", "method": "POST", "url": "...create_conexao" },
    { "ts": "...", "event": "http_response", "status": 200 }
  ],
  "events": [ "lista completa request/response filtrada" ]
}
```

---

## 3. Cenários (isolados — um browser por cenário)

| ID | Nome | O que testa |
|----|------|-------------|
| `manual` | Baseline ouro | Operador clica Confirmar (headful) |
| `ujs_click` | Hipótese UJS | `page.click('#seg_operador_conexao_btn_submit')` + `wait_for_response` |
| `legacy` | Reproduz bug | Enter + `document.forms[0].submit()` (switcher atual) |

**Hipótese central:** `legacy` → `create_conexao_post_count: 0`; `manual`/`ujs_click` → POST com CSRF.

---

## 4. Checklist de captura (por cenário)

### 4.1 Antes do commit

- [ ] `form_snapshot`: todos `seg_operador[...]` hidden
- [ ] `authenticity_token` presente no DOM? (meta vs input)
- [ ] `csrf_meta` valor completo
- [ ] `select2_labels` dos 3 containers
- [ ] `session_fingerprint` = últimos 12 chars `_vmx_saude_session` + CSRF meta
- [ ] `header_context` em `/` (baseline)

### 4.2 Durante seleção (dependência município)

Registrar na timeline cada `lookup_edit_v3` com:

- URL completa (especialmente `where=`)
- Ordem: município → unidade → setor
- Comparar cenário **com** re-select município vs **sem** (rodada extra opcional)

### 4.3 No commit

- [ ] Existe `POST .../create_conexao`?
- [ ] Body parseado: `authenticity_token`, `utf8`, `commit`, `seg_operador[codmunicipio|codunidade|codsetor|codoperador]`
- [ ] Headers: `X-CSRF-Token`, `X-Requested-With`
- [ ] Response status + primeiros 2KB body
- [ ] `Location` header se 302
- [ ] Body contém `window.location`, `redirect_to`, erros 422?

### 4.4 Após commit (sinais de persistência)

| Sinal | Como medir | Persistido se |
|-------|------------|---------------|
| HTTP | status 200/302 no POST | sim |
| Cookie | `_vmx_saude_session` mudou? | opcional |
| CSRF meta | token rotacionou? | opcional |
| Fingerprint | `session_fingerprint` mudou | forte |
| Header ERP | `#unidade_info` / `#setor_info` em `/` (barra `#bar_bottom`) | **obrigatório** |
| URL | saiu de `/conexao` ou desktop visível | suporte |

**Veredito `PERSISTED`:** POST ok **e** header bate com nomes Discovery para unit 14 / sector 10.

---

## 5. Arquivos a criar (modo Agent)

Copiar implementação abaixo para:

1. `backend/app/core/auth/adapters/playwright/trace/__init__.py`
2. `backend/app/core/auth/adapters/playwright/trace/commit_trace.py`
3. `backend/scripts/lab_context_commit_trace.py`

### 5.1 `commit_trace.py`

Ver repositório após merge Agent — módulo `CommitTraceCollector` com:

- Filtro URL: `create_conexao|lookup_edit_v3|/seg/operador|/login`
- `post_data_parsed` via `urllib.parse.parse_qs`
- `build_session_snapshot`, `extract_conexao_form_snapshot`

### 5.2 `lab_context_commit_trace.py` (especificação)

```
CLI:
  --scenario {manual,ujs_click,legacy,all}
  --unit-id 14 --sector-id 10 --municipality-id 3128253
  --headed (obrigatório para manual)
  --reselect-municipality (flag A/B test)

Fluxo comum:
  1. login (settings VIVVER_USER/PASS)
  2. attach CommitTraceCollector
  3. goto /seg/operador/conexao
  4. snapshot BEFORE (form + session; header em /)
  5. fill: opcional município → unidade → wait lookup setor → setor
  6. snapshot PRE_COMMIT
  7. executar estratégia do cenário
  8. wait até 30s por response create_conexao (ou timeout)
  9. snapshot AFTER
  10. save JSON + playwright trace.stop

Estratégias commit:
  legacy: focus #seg_operador_conexao_btn_submit + Enter; se URL ainda /conexao → forms[0].submit()
  ujs_click: click #seg_operador_conexao_btn_submit com expect_response **/create_conexao**
  manual: input() "Pressione Confirmar no browser e Enter aqui"
```

---

## 6. Comandos

```bash
cd backend

# Baseline humano (browser visível)
python -m scripts.lab_context_commit_trace --scenario manual --headed

# Reproduz bug atual
python -m scripts.lab_context_commit_trace --scenario legacy

# Teste UJS puro
python -m scripts.lab_context_commit_trace --scenario ujs_click

# Todos (3 browsers sequenciais)
python -m scripts.lab_context_commit_trace --scenario all
```

Requisitos: `VIVVER_USER` e `VIVVER_PASS` em `backend/.env`.

---

## 7. Matriz de decisão pós-forense

| Resultado | Conclusão | Próximo passo (Fase 2) |
|-----------|-----------|------------------------|
| legacy=0 POST, manual=1 POST | Bug confirmado: bypass UJS | `ConexaoCommitClient` via POST canônico |
| legacy=1 POST sem token, 422 | CSRF obrigatório no body | Injetar `authenticity_token` do meta |
| ujs_click=1 POST, header ok | Click UJS suficiente | Trocar switcher para click + wait response |
| Todos POST ok, header falha | Servidor aceita mas não persiste sessão | Investigar response JS / segundo request |
| Sem município vs com município diff | Dependência confirmada | Sempre re-select 3128253 |

---

## 8. Bloqueio atual

Implementação Python **requer modo Agent** no Cursor (modo Plan só permite markdown).  
Após liberar Agent: criar os 3 arquivos, rodar cenários, preencher [COMMIT_PROTOCOL.md](./COMMIT_PROTOCOL.md) §5.

**Para destravar:** no chat, enviar `execute a Fase 1` ou aceitar troca para modo Agent.
