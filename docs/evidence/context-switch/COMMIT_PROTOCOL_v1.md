# Context Commit Protocol v1 — Vivver `create_conexao`

**Versão:** 1.0  
**Data de estabilização:** 15/05/2026  
**Status:** Implementado em `ConexaoCommitClient` + `PlaywrightContextSwitcher`  
**Supersedes:** seções operacionais de [COMMIT_PROTOCOL.md](./COMMIT_PROTOCOL.md) (Fase 1 forense)

---

## 1. Escopo

Este documento formaliza o **único caminho institucional** pelo qual o Vivver persiste a combinação **Município + Unidade + Setor** para um operador autenticado.

Fora deste protocolo, qualquer estado de formulário ou Select2 é **não autoritativo**.

---

## 2. Endpoint real

| Campo | Valor |
|-------|--------|
| Método | `POST` |
| Path | `/seg/operador/{codoperador}/create_conexao` |
| URL absoluta | `https://{tenant}.vivver.com/seg/operador/{codoperador}/create_conexao` |
| `codoperador` | Hidden `seg_operador[codoperador]` (ex.: `{codoperador}` → `1659` anonimizado) |
| Resource type | `xhr` (Rails UJS) |
| Formulário origem | `#edit_seg_operador_{codoperador}` com `data-remote="true"` |
| Botão | `#seg_operador_conexao_btn_submit` (`remote="true"`) |

**Página de manobra:** `GET /seg/operador/conexao`

---

## 3. Headers obrigatórios

Exemplo anonimizado (trace `ujs_click`, 15/05/2026):

```http
POST /seg/operador/{codoperador}/create_conexao HTTP/1.1
Host: guaraciama-mg.vivver.com
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
X-Requested-With: XMLHttpRequest
X-CSRF-Token: VhKBVBrs9HCTpV1eJlZr…[REDACTED]
Accept: */*;q=0.5, text/javascript, application/javascript, ...
```

| Header | Obrigatório | Origem |
|--------|-------------|--------|
| `X-CSRF-Token` | Sim | `<meta name="csrf-token" content="…">` |
| `X-Requested-With` | Sim | `XMLHttpRequest` (Rails UJS) |
| `Content-Type` | Sim | `application/x-www-form-urlencoded; charset=UTF-8` |
| `Accept` | Sim | Aceita `text/javascript` na resposta |

**Nota:** `authenticity_token` **não** aparece no body neste ERP; o CSRF via header é suficiente (confirmado em forense).

---

## 4. Payload correto

### 4.1 Corpo `application/x-www-form-urlencoded` (exemplo Almoxarifado 14/10)

```text
utf8=✓
page=
seg_operador[codoperador]={codoperador}
lookup_key[seg_operador[codmunicipio]]=3128253
seg_operador[codmunicipio]=3128253
lookup_key[seg_operador[codunidade]]=14
seg_operador[codunidade]=14
lookup_key[seg_operador[codsetor]]=10
seg_operador[codsetor]=10
commit=Confirmar
```

### 4.2 Exemplo PSF + ATENDIMENTO (`sector_id=0`)

```text
lookup_key[seg_operador[codsetor]]=0
seg_operador[codsetor]=0
seg_operador[codunidade]=2
lookup_key[seg_operador[codunidade]]=2
…
commit=Confirmar
```

### 4.3 Campos obrigatórios (checklist pré-commit)

| Campo | Obrigatório |
|-------|-------------|
| `utf8` | Sim (`✓`) |
| `seg_operador[codoperador]` | Sim |
| `seg_operador[codmunicipio]` | Sim |
| `lookup_key[seg_operador[codmunicipio]]` | Sim (espelho) |
| `seg_operador[codunidade]` | Sim |
| `lookup_key[seg_operador[codunidade]]` | Sim |
| `seg_operador[codsetor]` | Sim (pode ser `0`) |
| `lookup_key[seg_operador[codsetor]]` | Sim |
| `commit` | Sim (`Confirmar`) |
| `page` | Presente (vazio ok) |

Validação em código: `ConexaoCommitClient.validate_form_ready()`.

---

## 5. Semântica `lookup_key`

O Vivver usa **fwk-lookup-edit-v3**: além do hidden `seg_operador[cod*]`, exige o campo texto `lookup_key[seg_operador[cod*]]` com o **mesmo código**.

| Hidden ID | Lookup key field ID |
|-----------|---------------------|
| `#seg_operador_codmunicipio` | `#lookup_key_seg_operador_codmunicipio` |
| `#seg_operador_codunidade` | `#lookup_key_seg_operador_codunidade` |
| `#seg_operador_codsetor` | `#lookup_key_seg_operador_codsetor` |

**Ordem de dependência (masters):**

1. Município → `codoperador`
2. Unidade → `codmunicipio`, `codoperador`
3. Setor → `codmunicipio`, `codunidade`, `codoperador`

XHR de descoberta (referência):

```http
GET /fwk/lookup_edit_v3?model=Seg::Operador::ConexaoQuery.search.distinct
  &key=codsetor&name=nomsetor
  &where=,codmunicipio=3128253,codunidade=14,codoperador={codoperador}
```

**HealthOps:** `discovery_client.list_sectors` deve incluir `codmunicipio` no `where`.

**Pré-commit:** `_sync_lookup_keys()` em `context_switcher.py` espelha os três pares via JS.

---

## 6. Semântica CSRF

| Mecanismo | Uso no Vivver |
|-----------|----------------|
| `<meta name="csrf-token">` | Fonte do valor |
| Header `X-CSRF-Token` | Enviado no POST xhr |
| `<input name="authenticity_token">` | **Ausente** no DOM capturado |
| Cookie de sessão | `_vmx_saude_session` — rotaciona após sucesso |

Extração pós-login: `PlaywrightSessionManager.extract_csrf_token()`.

---

## 7. Rotação de cookie / sessão

**Fingerprint operacional:**

```text
session_fingerprint = last12(_vmx_saude_session) + ":" + last12(csrf_meta)
```

**Regra v1:** após commit bem-sucedido, `session_fingerprint` **deve** diferir do valor `before`.

Implementação: `build_session_snapshot()` em `commit_trace.py`.

Cookies relevantes:

| Cookie | Papel |
|--------|--------|
| `_vmx_saude_session` | Sessão Rails — **rotaciona** no sucesso |
| `auth_token` | Autenticação complementar |

---

## 8. Resposta esperada

| Atributo | Valor esperado |
|----------|----------------|
| HTTP status | `200` |
| `Content-Type` | `text/javascript; charset=utf-8` |
| Corpo | HTML/JS embutido com `alert-success` e texto **`Conexão ativada com sucesso`** |
| `x-request-id` | Presente (correlação servidor) |

Trecho anonimizado (response body preview):

```javascript
// …
<div class="fwk-alert-message alert alert-success">
  Conexão ativada com sucesso
  …
</motion.div>
```

**Validação em código:** `SUCCESS_MARKER = "Conexão ativada com sucesso"` em `conexao_commit.py`.

---

## 9. Sinais soberanos de persistência

A troca **só é considerada persistida** quando **todas** as condições abaixo são verdadeiras:

| # | Sinal | Implementação |
|---|--------|----------------|
| 1 | Exatamente **1** POST `create_conexao` (xhr) na janela da manobra | Trace / `CommitResult.post_count` |
| 2 | Status HTTP 2xx + marcador de sucesso no body | `ConexaoCommitClient.commit()` |
| 3 | `session_fingerprint` alterado | `context_switcher` before/after |
| 4 | Barra `#unidade_info` / `#setor_info` reflete IDs alvo | `read_desktop_bar_context()` |
| 5 | (Opcional) Nomes cruzados com Discovery | `enrich_context_labels()` |

**Não usar como primário:** Select2 label, estado do modal HealthOps, `GET /current` nos primeiros 60s pós-switch sem guard.

---

## 10. Failure modes conhecidos

| Código | Causa | Sintoma |
|--------|--------|---------|
| `COMMIT_NOT_SENT` | Click sem response xhr | Timeout `expect_response` |
| `COMMIT_REJECTED` | HTTP 4xx/5xx | Body salvo em `last_switch_commit.json` |
| `COMMIT_RESPONSE_INVALID` | 200 sem mensagem de sucesso | POST saiu mas ERP não confirmou |
| `FORM_NOT_READY` | Hidden/lookup_key ausente | Pré-validação falhou |
| `MUNICIPALITY_NOT_FOUND` | Lookup município | Hidden não bate |
| `UNIT_NOT_FOUND` | Lookup unidade | — |
| `SECTOR_NOT_FOUND` | Lookup setor | — |
| `SWITCH_NOT_PERSISTED` | Fingerprint igual | POST duvidoso |
| `SECTOR_REQUIRED` | API sem sector_id | Antes do Playwright |
| `MULTIPLE_CHOICES_REQUIRED` | Vários setores sem escolha | ~2s; inclui bug histórico `sector_id=0` |
| `AUTH_EXPIRED` | Redirect login | — |
| `REVALIDATION_FAILED` | Exceção na manobra (ex. `ERR_ABORTED`) | Mitigado por `safe_goto_home` |

**Anti-padrão proibido:** `document.forms[0].submit()` — gera POST document paralelo (ver `legacy_trace.json`).

---

## 11. Correlation timeline (exemplo `ujs_click`)

| ts (UTC) | event | detalhe |
|----------|-------|---------|
| 11:46:41 | `http_request` | GET `/login` |
| 11:46:4x | `http_request` | GET `/seg/operador/conexao` |
| 11:46:4x | `http_request` | GET `lookup_edit_v3` (cadeia município→unidade→setor) |
| 11:46:53.236 | `http_request` | **POST** `create_conexao` (xhr) |
| 11:46:53.508 | `http_response` | **200** `text/javascript` + sucesso |
| 11:46:5x | `session_fingerprint` | valor **after** ≠ before |
| 11:46:5x | `bar_read` | `#unidade_info` = `14 - ALMOXARIFADO…` |

Fonte completa: [`backend/evidence/context-switch/ujs_click_trace.json`](../../../backend/evidence/context-switch/ujs_click_trace.json) → chave `timeline`.

---

## 12. Implementação HealthOps

| Componente | Arquivo |
|------------|---------|
| Commit | [`conexao_commit.py`](../../../backend/app/core/auth/adapters/playwright/clients/conexao_commit.py) |
| Manobra | [`context_switcher.py`](../../../backend/app/core/auth/adapters/playwright/clients/context_switcher.py) |
| Trace / snapshot | [`commit_trace.py`](../../../backend/app/core/auth/adapters/playwright/trace/commit_trace.py) |
| API | [`session.py`](../../../backend/app/api/v1/session.py) |
| Lab | `backend/scripts/lab_context_commit_trace.py` |

---

## 13. Referências

- [ROOT_CAUSE_ANALYSIS.md](./ROOT_CAUSE_ANALYSIS.md)
- [VALIDATED_SCENARIOS.md](./VALIDATED_SCENARIOS.md)
- [PHASE1_FORENSIC_RUNBOOK.md](./PHASE1_FORENSIC_RUNBOOK.md)
