# Portas oficiais — desenvolvimento local (HealthOps Almox)

**Objetivo:** uma única convenção para máquina dev, evitando `8000` vs `8001`, `localhost` vs `127.0.0.1`, e “duas APIs ao mesmo tempo sem querer”.

**Última revisão:** 2026-05-15

---

## 1. Convenção fixa

| Serviço | Porta | URL típica |
|---------|-------|------------|
| **Backend (FastAPI / uvicorn)** | **8000** | `http://127.0.0.1:8000` |
| **Frontend (Vite)** | **5173** | `http://localhost:5173` *(recomendado — ver §4)* |
| **PostgreSQL** | conforme `backend/.env` | (ex.: `5434`) |

**Não** usar `8001` para a API neste fluxo — URLs e proxy do Vite assumem **8000**.

---

## 2. Ordem obrigatória de arranque

Subir **nesta ordem**, sempre:

1. **Backend** — `uvicorn` na **8000** (contém o fluxo que **lança o Playwright/Chromium** quando precisa falar com o Vivver).  
2. **Playwright** — **não é um terceiro servidor HTTP separado** no nosso desenho; significa:
   - uma vez por venv: `playwright install chromium` (ver [RELEASE_HANDOFF](evidence/context-switch/RELEASE_HANDOFF.md));
   - garantir que o **backend já está de pé** antes de qualquer operação que force login/troca Vivver (o browser controlado nasce **dentro do processo backend**).
3. **Frontend** — `npm run dev` na **5173**, **depois** da API estar a responder (ex.: `/docs`).

Assim evitamos “UI a bater em API que ainda está a autenticar / ainda não existe”.

---

## 3. Variáveis `.env` alinhadas

**`frontend/.env`** (modo real):

```env
VITE_APP_MODE=PRODUCTION
VITE_API_URL=http://127.0.0.1:8000
```

Depois de mudar `VITE_*`, **reiniciar** o Vite.

O **proxy** do Vite (`/almox` → backend) em `frontend/vite.config.js` deve apontar para **127.0.0.1:8000**.

---

## 4. Vite: `localhost` vs `127.0.0.1`

O `server.host` do Vite está configurado para responder em **IPv4 e IPv6**, evitando o caso em que o dev server só escuta em `::1` e pedidos a `127.0.0.1:5173` falham.

- Preferir abrir a UI em **`http://localhost:5173`**.

---

## 5. `playwright install` — uma vez por venv, não a cada restart

| Pergunta | Resposta |
|----------|----------|
| Preciso de `playwright install chromium` **toda vez** que reinicio o uvicorn? | **Não.** Só quando criar/actualizar o `.venv` ou mudar versão do Playwright. |
| O que se perde ao **reiniciar o servidor**? | A **sessão em memória** (browser Playwright no processo). A primeira chamada a `/session/current` faz **login de novo** no Vivver (~15–90 s). |
| Isso é o mesmo que “reinstalar Playwright”? | **Não.** Reinício = novo login ERP; install = binários do Chromium no disco. |

Comando (uma vez no venv do backend):

```bash
cd backend
.\.venv\Scripts\playwright.exe install chromium
```

---

## 6. Erro 401 / `NotImplementedError` vazio

**Sintoma:** `Detalhe: NotImplementedError:` sem mais texto.

**Causa frequente no Windows:** o processo do uvicorn está com **WindowsSelectorEventLoopPolicy**; o Playwright precisa de **Proactor** (subprocessos). O código em `app/main.py` força Proactor no arranque — **reinicie o uvicorn** depois de actualizar.

**Checklist:**

1. Pare **todos** os `python`/uvicorn na porta **8000** (evite dois servidores em conflito).  
2. Suba só com: `backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000` (cwd = `backend`).  
3. `GET http://127.0.0.1:8000/almox/v1/session/diagnostics` → `asyncio_policy` deve ser **`WindowsProactorEventLoopPolicy`**.  
4. Se ainda 401: `POST http://127.0.0.1:8000/almox/v1/session/reset-erp` e depois `GET /current` de novo.

---

## 7. Erro 401 / “Failed to resolve real ERP context” (geral)

**Situação atual (esperada após endurecimento):** o sistema **distingue** falha de rede (backend inacessível) de **sessão/contexto ERP inválido** — isto é **progresso**: antes parecia “tudo partido”; agora o estado inválido aparece de forma explícita.

**Primeira ação (ordem do time):**

1. **Relogin / reautenticar no fluxo Vivver via backend** (credenciais, sessão ERP expirada, Playwright não autenticado).  
2. Confirmar env: `VIVVER_USER`, `VIVVER_PASS`, `VIVVER_OPERATOR_ID`, URLs Vivver — ver handoff.

**Evitar:**

- **Não** “refatorar o frontend para esconder o 401” como primeira reação — o sintoma já está **corretamente detectado**; tratar é **motor de sessão + ERP**, não cosmética de UI.

Se após relogar o problema persistir, seguir evidência em [docs/evidence/context-switch/](evidence/context-switch/README.md).

---

## 8. Checklist rápido quando “não conecta”

- [ ] Só existe **uma** instância canónica na **8000** (evitar dois `uvicorn` em portas diferentes por hábito).  
- [ ] `curl http://127.0.0.1:8000/docs` → 200  
- [ ] `curl -s http://127.0.0.1:8000/almox/v1/session/current` → **200** com `data` (se vier **401** com texto sobre Vivver, o problema não é porta: é login Playwright ou `.env`; ver traceback no terminal do **uvicorn** no instante da chamada).  
- [ ] `frontend/.env` com `VITE_API_URL=http://127.0.0.1:8000` e Vite reiniciado  
- [ ] Frontend aberto em `http://localhost:5173`

---

## 9. Documentos relacionados

- Arranque detalhado: [RELEASE_HANDOFF.md](evidence/context-switch/RELEASE_HANDOFF.md)  
- Orientação IA: [AI_SESSION_START_HERE.md](AI_SESSION_START_HERE.md)  
- Baseline UI: [FRONTEND_BASELINE_PROTOCOL.md](core-platform/FRONTEND_BASELINE_PROTOCOL.md)
