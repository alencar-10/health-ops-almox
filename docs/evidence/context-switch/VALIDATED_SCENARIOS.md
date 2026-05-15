# Validated Scenarios — Context Switch

**Data de validação:** 15/05/2026  
**Ambiente:** backend `py -3.13`, `http://127.0.0.1:8000`, Vivver Guaraciama-MG  
**Operador:** credenciais de sistema em `settings` (não documentadas aqui)

---

## Critérios globais de aceite

Uma troca é **válida** quando:

1. `POST /almox/v1/session/switch` retorna `status: COMPLETED`
2. `GET /almox/v1/session/current` reflete `unit` e `sector` alvo (IDs e nomes)
3. (Manual opcional) barra Vivver `#unidade_info` / `#setor_info` confere

---

## Cenário 1 — PSF + ATENDIMENTO (`sector_id=0`)

| Campo | Valor |
|-------|--------|
| `unit_id` | `2` |
| `unit_name` | PSF SAUDE PARA TODOS |
| `sector_id` | `0` |
| `sector_name` | ATENDIMENTO |
| Status API | `COMPLETED` |
| Tempo observado | **~24s** (cold, com login); **~5s** (warm) |

**Regressão documentada (pré-fix):**

```bash
curl -s -X POST "http://127.0.0.1:8000/almox/v1/session/switch?unit_id=2&sector_id=0"
# → MULTIPLE_CHOICES_REQUIRED em ~2s
# → /current permanece unit 14
```

**Pós-fix:**

```bash
curl -s -X POST "http://127.0.0.1:8000/almox/v1/session/switch?unit_id=2&sector_id=0"
curl -s "http://127.0.0.1:8000/almox/v1/session/current"
# → unit.id=2, sector.id=0
```

---

## Cenário 2 — Almoxarifado (`14/10`)

| Campo | Valor |
|-------|--------|
| `unit_id` | `14` |
| `unit_name` | ALMOXARIFADO DA SAUDE |
| `sector_id` | `10` |
| `sector_name` | ALMOXARIFADO |
| Status API | `COMPLETED` |
| Tempo observado | **~20s** |

Este cenário funcionava **antes** do fix `sector_id=0`, o que reforçou a hipótese semântica (não genérica de Playwright).

---

## Cenário 3 — Roundtrip entre unidades

| Passo | Params | Resultado |
|-------|--------|-----------|
| A | `2/0` PSF | `COMPLETED` |
| B | `14/10` Almoxarifado | `COMPLETED` (~20s) |
| C | `2/0` PSF novamente | `COMPLETED` (~5s) |

**Nota operacional:** passo B falhou uma vez com `REVALIDATION_FAILED` / `net::ERR_ABORTED` em `goto` home **antes** de `safe_goto_home()`. Após mitigação, roundtrip estável.

---

## Cenário 4 — Persistência pós-refresh

| Verificação | Método | Esperado |
|-------------|--------|----------|
| Sessão HealthOps | `GET /current` após switch | IDs corretos |
| Barra ERP | Navegar `/` no browser Vivver | `#unidade_info` / `#setor_info` |
| Cookie | `session_fingerprint` mudou no trace | before ≠ after |

**Lab reproduzível:**

```bash
cd backend
py -3.13 -m scripts.lab_context_commit_trace --scenario ujs_click --unit-id 14 --sector-id 10
```

Artefato: `backend/evidence/context-switch/ujs_click_trace.json`.

---

## Cenário 5 — Rotação de sessão

| Métrica | Before | After (commit ok) |
|---------|--------|-------------------|
| `_vmx_saude_session` | valor A | valor B (≠ A) |
| `session_fingerprint` | `…:csrf_a` | `…:csrf_b` |

Fonte: `build_session_snapshot()` em commits bem-sucedidos; ver `summary` nos traces JSON.

---

## Cenário 6 — Falha explícita (negociação)

| Condição | Resultado esperado |
|----------|-------------------|
| `sector_id` omitido + unidade com 2+ setores | `MULTIPLE_CHOICES_REQUIRED` |
| Form sem `lookup_key` | `FORM_NOT_READY` / manobra abortada |
| Commit sem POST xhr | `COMMIT_NOT_SENT` |

**Tempo:** falhas de resolução API **< 3s** (sem Playwright).

---

## Tempos médios observados (resumo)

| Tipo | Duração típica |
|------|----------------|
| Falha API (sector não resolvido) | 1–3 s |
| Switch warm (sessão Playwright ativa) | 5–10 s |
| Switch cold (login + discovery + manobra) | 20–30 s |
| Lab trace `ujs_click` completo | ~12 s (login + manobra) |

---

## Checklist UI (PRODUCTION)

- [ ] `VITE_APP_MODE=PRODUCTION`, `VITE_API_URL=http://localhost:8000`
- [ ] Backend Python **3.13**
- [ ] TopBar: PSF → ATENDIMENTO permanece após overlay
- [ ] Retorno Almoxarifado 14/10 sem travar overlay
- [ ] Erro `MULTIPLE_CHOICES_REQUIRED` visível (não revert silencioso)

---

## Referências

- [COMMIT_PROTOCOL_v1.md](./COMMIT_PROTOCOL_v1.md)
- [ROOT_CAUSE_ANALYSIS.md](./ROOT_CAUSE_ANALYSIS.md)
- Scripts: `lab_context_switch_integration.py`, `lab_context_commit_trace.py`
