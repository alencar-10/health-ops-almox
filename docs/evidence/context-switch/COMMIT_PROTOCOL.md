# Protocolo de Commit: Troca de Contexto Vivver (`create_conexao`)

> **Histórico (Fase 1 forense).** Contrato operacional estabilizado: **[COMMIT_PROTOCOL_v1.md](./COMMIT_PROTOCOL_v1.md)**.  
> Índice institucional: **[README.md](./README.md)**.

**Data:** 15/05/2026  
**Status:** Fase 1 runtime concluída (15/05/2026) — ver artefatos em `backend/evidence/context-switch/`  
**Fontes:** `backend/last_switch_error.html`, `CONTEXT_SWITCH_DIAGNOSIS.md`, `context_switcher.py`

---

## 1. Resumo executivo

O formulário de conexão é preenchido corretamente, mas a **persistência no servidor** falha porque o fluxo atual de automação provavelmente **não dispara o POST remoto Rails UJS** que o Vivver espera.

| Hipótese | Confiança | Evidência |
|----------|-----------|-----------|
| `document.forms[0].submit()` bypassa UJS | Alta | Form `data-remote="true"`; código L129 em `context_switcher.py` |
| POST `create_conexao` nunca sai ou sai sem CSRF | Alta | HTML de erro sem `authenticity_token` no DOM; só meta CSRF |
| Espera por `domcontentloaded` após submit remoto | Alta | Remote forms não navegam; wait é irrelevante |
| Município não re-selecionado na manobra | Média | Switcher só mexe em unidade/setor; relatório sugere cadeia master |

**Próximo passo obrigatório:** rodar `backend/scripts/lab_context_commit_trace.py` (a ser criado no modo Agent) e preencher a seção 5 deste documento com HAR real.

---

## 2. Contrato do formulário (análise estática)

### 2.1 Endpoint

| Atributo | Valor (snapshot de erro) |
|----------|--------------------------|
| URL da página | `/seg/operador/conexao` |
| `action` | `/seg/operador/1659/create_conexao` |
| `method` | `POST` |
| `data-remote` | `true` (Rails UJS / jQuery AJAX) |
| Botão submit | `#seg_operador_conexao_btn_submit` (`remote="true"`) |

URL absoluta esperada:

`https://guaraciama-mg.vivver.com/seg/operador/{codoperador}/create_conexao`

`codoperador` vem do hidden `seg_operador[codoperador]` (ex.: `1659`).

### 2.2 Campos hidden / backing inputs (estado no erro)

| Campo POST | Valor no erro | Select2 label |
|------------|---------------|---------------|
| `seg_operador[codoperador]` | `1659` | — |
| `seg_operador[codmunicipio]` | `3128253` | GUARACIAMA |
| `seg_operador[codunidade]` | `14` | ALMOXARIFADO DA SAUDE |
| `seg_operador[codsetor]` | `10` | ALMOXARIFADO |
| `utf8` | `✓` | — |
| `page` | *(vazio)* | — |
| `commit` | `Confirmar` | — |

**Ausente no DOM capturado:** `authenticity_token` como `<input hidden>`.  
**Presente no `<head>`:** `<meta name="csrf-token" content="...">`

Conclusão: o UJS provavelmente injeta `authenticity_token` e `X-CSRF-Token` apenas no pipeline `ajax:before` — commits que bypassam esse pipeline podem ser **ignorados silenciosamente** ou retornar 422.

### 2.3 Headers esperados (Rails remote)

Comparar na Fase 1 lab:

```
X-Requested-With: XMLHttpRequest
X-CSRF-Token: <valor do meta csrf-token>
Accept: */* ou text/javascript
Content-Type: application/x-www-form-urlencoded
```

### 2.4 Cadeia de dependência (lookups)

Ordem lógica dos masters (atributos `data-lookup-master`):

1. **Município** — master `:codoperador`
2. **Unidade** — master `:codmunicipio,:codoperador`
3. **Setor** — master `:codmunicipio,:codunidade,:codoperador`

XHR de descoberta (referência):

```
GET /fwk/lookup_edit_v3?model=Seg::Operador::ConexaoQuery.search.distinct
    &key=codsetor&name=nomsetor
    &where=,codmunicipio=3128253,codunidade=14,codoperador=1659
```

**Bug conhecido no HealthOps:** `discovery_client.list_sectors` usa `where=,codunidade={id}` sem `codmunicipio` — corrigir na Fase 2.

---

## 3. O que o código atual faz vs. o que deveria

### Fluxo atual (`PlaywrightContextSwitcher`)

```
goto /seg/operador/conexao
→ select2 unidade (ID)
→ sleep 2000ms
→ select2 setor OU primeiro da lista (heurística)
→ sleep 1000ms
→ focus submit + Enter
→ wait domcontentloaded (10s)
→ se ainda em /conexao: document.forms[0].submit()
→ wait load (20s)
→ wait .desktop OU goto / e checar header
```

### Problemas mapeados

| # | Problema | Impacto |
|---|----------|---------|
| 1 | `form.submit()` nativo | Não dispara UJS → **sem POST remoto** |
| 2 | `wait_for_load_state` após remote | Falso negativo; página não recarrega |
| 3 | `FALLBACK_FIRST_OPTION` | Setor errado possível; viola regra DEV |
| 4 | Não re-seleciona município | Pode deixar hidden incoerente com sessão |
| 5 | Validação `"ALMOXARIFADO" in unit_after` | Heurística silenciosa |
| 6 | Código após `return` L154 | `snapshot_after` nunca preenchido |

### Fluxo alvo (pós-forense)

```
goto /seg/operador/conexao
→ select2 município 3128253 (sempre)
→ wait response lookup_edit_v3 (unidades)
→ select2 unidade {unit_id}
→ wait response lookup_edit_v3 key=codsetor
→ select2 setor {sector_id} (obrigatório)
→ snapshot form + session_version ANTES
→ commit: POST create_conexao (protocolo verificado)
→ wait response create_conexao + session_version DEPOIS
→ goto / → validar `#unidade_info` / `#setor_info` (barra inferior) vs Discovery
```

---

## 4. Critérios de sucesso do commit (definição operacional)

A troca **só é persistida** quando **todas** forem verdadeiras:

1. Existe **exatamente um** `POST` para `*/create_conexao` com status `200` ou `302` na janela da manobra.
2. O body do POST contém `authenticity_token` **ou** header `X-CSRF-Token` igual ao meta da página.
3. `get_session_version()` (cookie + CSRF) **muda** após o POST.
4. Cabeçalho ERP em `/` exibe unidade/setor **nomes** correspondentes aos IDs solicitados (via Discovery).

Falha explícita se:

- Zero POST `create_conexao` → `COMMIT_NOT_SENT`
- POST 4xx/5xx → `COMMIT_REJECTED` + body salvo
- POST 200 mas header inalterado → `SWITCH_NOT_PERSISTED`

---

## 5. Evidência runtime (lab 15/05/2026)

Artefatos: `backend/evidence/context-switch/legacy_trace.json`, `ujs_click_trace.json`

### 5.1 Contrato canônico do commit (confirmado)

| Item | Valor |
|------|-------|
| URL | `POST /seg/operador/{codoperador}/create_conexao` (ex.: `1659`) |
| Tipo | `xhr` (Rails UJS) |
| CSRF | Header **`X-CSRF-Token`** = conteúdo de `<meta name="csrf-token">` |
| `authenticity_token` no body | **Não** enviado (null no DOM e ausente no payload) |
| Headers obrigatórios | `X-Requested-With: XMLHttpRequest`, `Content-Type: application/x-www-form-urlencoded; charset=UTF-8` |
| Resposta sucesso | `200` + `Content-Type: text/javascript` + mensagem **`Conexão ativada com sucesso`** no body |
| Sinal de sessão | `_vmx_saude_session` **muda** após POST bem-sucedido (`session_fingerprint` diferente) |

### 5.2 Payload completo (campos obrigatórios)

Além dos `seg_operador[...]`, o Vivver exige os pares **`lookup_key[...]`** espelhando os códigos:

```
utf8=✓
page=
seg_operador[codoperador]=1659
lookup_key[seg_operador[codmunicipio]]=3128253
seg_operador[codmunicipio]=3128253
lookup_key[seg_operador[codunidade]]=14
seg_operador[codunidade]=14
lookup_key[seg_operador[codsetor]]=10
seg_operador[codsetor]=10
commit=Confirmar
```

Sem `lookup_key[...]` ou sem `commit=Confirmar` o commit **não é equivalente** ao fluxo humano/UJS.

### 5.3 Cenário `ujs_click` (referência limpa)

| Métrica | Valor |
|---------|-------|
| POST create_conexao | **1** (xhr) |
| Status | **200** |
| X-CSRF-Token | Presente |
| Veredito | `PERSISTED` |
| Response snippet | `alert-success` → "Conexão ativada com sucesso" |

### 5.4 Cenário `legacy` (switcher atual — problema identificado)

| Métrica | Valor |
|---------|-------|
| POST create_conexao | **2** |
| POST #1 | xhr, com CSRF + `commit=Confirmar` (correto) |
| POST #2 | **document**, sem `X-CSRF-Token`, **sem** `commit=Confirmar` (fallback `forms[0].submit()`) |
| Veredito | `PERSISTED` neste run (sessão rotacionou) |

**Conclusão forense:** o Enter **às vezes** dispara o UJS (POST #1). O fallback nativo sempre dispara um segundo POST incompleto que pode causar **corrida / ignorar persistência** em outros runs — explica o comportamento intermitente do ERP.

### 5.5 Cenário `manual`

Não executado neste ciclo (requer `--headed`). Rodar localmente para baseline ouro.

### 5.6 Por que o ERP “ignora” o submit (hipóteses atualizadas)

1. **POST nunca sai** — formulário mal hidratado (falta `lookup_key`, setor/unidade errados) + Enter não aciona UJS.
2. **POST duplo** — xhr válido + document inválido (legacy) → estado inconsistente.
3. **POST sem CSRF** — apenas o segundo submit nativo → servidor rejeita ou não persiste.
4. **Validação no switcher** — header `.unidade_nome` retornou `N/A` na home (seletor pode diferir); usar rotação de cookie + response JS como sinais primários.

### 5.7 Implicação para Fase 2 (sem retries mágicos)

- Commit **único** via `page.click(#seg_operador_conexao_btn_submit)` + `wait_for_response(create_conexao)`.
- **Remover** `document.forms[0].submit()` permanentemente.
- Validar payload inclui `lookup_key[...]` + `commit=Confirmar` antes do POST.
- Fail-closed se `create_conexao_post_count != 1` ou body não contém "Conexão ativada com sucesso".
- Opcional: `page.request.post()` com payload espelhado se UJS falhar **uma** vez (sem loop).

---

## 6. Fase 1 — Laboratório de protocolo

**Runbook:** [PHASE1_FORENSIC_RUNBOOK.md](./PHASE1_FORENSIC_RUNBOOK.md)  
**Script:** `backend/scripts/lab_context_commit_trace.py`  
**Módulo trace:** `backend/app/core/auth/adapters/playwright/trace/commit_trace.py`

```bash
cd backend
pip install playwright pydantic-settings
playwright install chromium
python -m scripts.lab_context_commit_trace --scenario ujs_click --unit-id 14 --sector-id 10
```

### O que capturar (obrigatório)

| Categoria | Conteúdo |
|-----------|----------|
| HAR / network | Todos `create_conexao` + `lookup_edit_v3` request/response |
| Payload | `post_data_parsed` com todos `seg_operador[...]` + `authenticity_token` |
| Headers | `X-CSRF-Token`, `X-Requested-With`, `Content-Type` |
| Cookies | `_vmx_saude_session`, `auth_token` before/after |
| Snapshots | Form DOM + header `.unidade_nome` / `.setor_nome` |
| Timeline | Correlação: navigate → selects → lookups → commit → validate |

### Cenários isolados

1. **manual** — baseline ouro (POST real humano)
2. **ujs_click** — só click no Confirmar + wait response
3. **legacy** — reproduz `context_switcher.py` (Enter + `forms[0].submit()`)

### Comando (após criar scripts no modo Agent)

```bash
cd backend
python -m scripts.lab_context_commit_trace --scenario all --unit-id 14 --sector-id 10 --municipality-id 3128253
```

**Fase 2 implementada** — ver `conexao_commit.py` + `context_switcher.py` refatorado.

---

## 7. Referências

- [CONTEXT_SWITCH_DIAGNOSIS.md](../../../CONTEXT_SWITCH_DIAGNOSIS.md)
- [ADR-004 Context Switching](../../architecture/decisions/ADR-004-context-switching.md)
- [session_context_rules.md](../../../frontend/docs/business_rules/session_context_rules.md)
- [context_switcher.py](../../../backend/app/core/auth/adapters/playwright/clients/context_switcher.py)
