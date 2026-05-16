# Instruções para IA — servidores locais (parar, iniciar, reiniciar)

**Público:** agentes de IA (Antigravity, Cursor, etc.) e operadores que delegam tarefas à IA.  
**Objetivo:** evitar erros recorrentes (porta errada, Python errado, dois uvicorn, `NotImplementedError`, “funcionou no curl mas a UI falha”).

**Leitura prévia obrigatória:** [OFFICIAL_LOCAL_PORTS.md](./OFFICIAL_LOCAL_PORTS.md) · [AI_SESSION_START_HERE.md](./AI_SESSION_START_HERE.md)

---

## 1. Regras de ouro (nunca violar)

| # | Regra |
|---|--------|
| 1 | **Backend = porta `8000`**, **Frontend = porta `5173`**. Não usar `8001` para a API canónica. |
| 2 | **Sempre** subir o backend a partir da pasta **`backend/`** com **`backend\.venv\Scripts\python.exe`**. Nunca assumir `.venv` na raiz do repositório (não existe). |
| 3 | **Ordem de arranque:** (1) libertar portas → (2) **backend** → (3) aguardar `/docs` 200 → (4) **frontend**. |
| 4 | **`playwright install chromium`** — **uma vez por venv**, não a cada restart do uvicorn. |
| 5 | **Reiniciar o uvicorn** = perde a sessão Playwright em memória; a **primeira** `GET /session/current` faz login de novo (~15–90 s). Isso é **normal**, não é “reinstalar Playwright”. |
| 6 | **Não** diagnosticar sessão Vivver com URLs `chrome-extension://` ou ficheiros `.css` da extensão do browser — o endpoint é **`http://127.0.0.1:8000/almox/v1/session/current`**. |
| 7 | **Não** “refatorar o frontend” quando o utilizador reporta **401** — primeiro: backend no ar, credenciais `.env`, relogin ERP (`/reset-erp` + `/current`). |
| 8 | No Windows, o código **exige** `WindowsProactorEventLoopPolicy` (já forçado em `app/main.py`). Se aparecer `NotImplementedError` vazio no login, o processo em execução pode ser **uvicorn antigo** ou **Python errado** — reiniciar com o procedimento abaixo. |

---

## 2. Variáveis e ficheiros que a IA deve conhecer

| Ficheiro | Conteúdo relevante |
|----------|-------------------|
| `backend/.env` | `VIVVER_USER`, `VIVVER_PASS`, `VIVVER_URL`, `VIVVER_OPERATOR_ID`, `APP_MODE=PRODUCTION`, DB |
| `frontend/.env` | `VITE_APP_MODE=PRODUCTION`, `VITE_API_URL=http://127.0.0.1:8000` |
| `frontend/vite.config.js` | Proxy `/almox` → `127.0.0.1:8000` |

**Após alterar `frontend/.env` (`VITE_*`):** o utilizador (ou a IA) deve **reiniciar o Vite** (`npm run dev`).

**Após alterar `backend/.env`:** reiniciar o **uvicorn** (o `get_settings()` está em cache no processo).

---

## 3. Verificar o que está a correr (antes de mudar qualquer coisa)

Executar no PowerShell (Windows):

```powershell
Get-NetTCPConnection -LocalPort 8000,5173 -State Listen -ErrorAction SilentlyContinue |
  Format-Table LocalPort, OwningProcess, State -AutoSize
```

Interpretação:

- **8000** — deve haver **no máximo um** `OwningProcess` em `Listen`. Vários = conflito (UI pode bater no processo errado).
- **5173** — Vite (frontend).

Smoke rápido (backend):

```powershell
curl -s -o NUL -w "docs: %{http_code}`n" http://127.0.0.1:8000/docs
curl -s http://127.0.0.1:8000/almox/v1/session/diagnostics
```

Em `diagnostics`, confirmar:

- `asyncio_policy` = **`WindowsProactorEventLoopPolicy`**
- `python_executable` contém **`backend\.venv\Scripts\python.exe`**
- `app_mode` = **`PRODUCTION`** (se o utilizador estiver a testar Vivver real)

---

## 4. Parar servidores (desligar)

### 4.1 O que a IA deve fazer

1. Identificar PIDs nas portas **8000** e **5173** (comando da secção 3).
2. Encerrar **esses** processos — não fazer `taskkill` genérico em todos os `python.exe` do sistema **a menos que o utilizador peça explicitamente** (pode matar outros projetos).

```powershell
# Substituir <PID> pelos valores da porta 8000 e 5173
Stop-Process -Id <PID> -Force -ErrorAction SilentlyContinue
```

3. Aguardar ~2 s e confirmar que **8000** e **5173** já não estão em `Listen`.

### 4.2 O que dizer ao utilizador

- “Parei o backend (8000) e o frontend (5173). A sessão Vivver em memória foi libertada; no próximo arranque o primeiro `/current` volta a fazer login no ERP.”

### 4.3 Erros a evitar

- Deixar um uvicorn fantasma na 8000 e subir outro → `WinError 10048` (porta em uso) ou comportamento aleatório.
- Assumir que “parar o terminal” no IDE sempre mata o processo — por vezes não mata; **confirmar com `Get-NetTCPConnection`**.

---

## 5. Iniciar servidores (primeira vez ou após parar)

### 5.1 Ordem obrigatória

```
[1] Libertar portas 8000/5173 se ocupadas
[2] Backend (uvicorn) — backend/ + venv
[3] Esperar /docs → 200
[4] Frontend (Vite) — frontend/
[5] Smoke: diagnostics + (opcional) /session/current
[6] Pedir ao utilizador: abrir http://localhost:5173 e Ctrl+Shift+R
```

### 5.2 Backend — comando canónico

**Opção A (recomendada):**

```powershell
cd C:\caminho\para\health-ops-almoxarifado\backend
.\scripts\start-backend.ps1
```

**Opção B (equivalente):**

```powershell
cd C:\caminho\para\health-ops-almoxarifado\backend
Remove-Item Env:PLAYWRIGHT_BROWSERS_PATH -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Manter este processo **em execução** (terminal em background ou dedicado).

**Nunca:**

```powershell
# ERRADO — não há .venv na raiz
cd health-ops-almoxarifado
.\.venv\Scripts\python.exe -m uvicorn app.main:app ...
```

```powershell
# ERRADO — Python global pode não ter Playwright/browsers alinhados
python -m uvicorn app.main:app --port 8000
```

### 5.3 Frontend — comando canónico

```powershell
cd C:\caminho\para\health-ops-almoxarifado\frontend
npm run dev
```

Abrir no browser: **`http://localhost:5173`** (preferir `localhost` a `127.0.0.1` no Vite).

### 5.4 Playwright (só se nunca instalado neste venv)

```powershell
cd backend
.\.venv\Scripts\playwright.exe install chromium
```

Não repetir a cada arranque do uvicorn.

### 5.5 Validação que a IA deve executar antes de dizer “está pronto”

| Passo | Comando | Esperado |
|-------|---------|----------|
| API viva | `curl http://127.0.0.1:8000/docs` | HTTP 200 |
| Diagnóstico | `curl http://127.0.0.1:8000/almox/v1/session/diagnostics` | `WindowsProactorEventLoopPolicy`, venv |
| Sessão (1ª vez) | `curl -m 120 http://127.0.0.1:8000/almox/v1/session/current` | HTTP 200 com `data` (pode demorar) |
| UI | `curl -o NUL -w "%{http_code}" http://localhost:5173/` | HTTP 200 |

---

## 6. Reiniciar servidores (o utilizador quer “reiniciar para testar”)

### 6.1 Procedimento completo (copiar para o agente)

1. **Parar** backend (8000) e frontend (5173) — secção 4.  
2. Confirmar portas livres.  
3. **Iniciar** backend — secção 5.2; aguardar log `Uvicorn running on http://127.0.0.1:8000`.  
4. **Iniciar** frontend — secção 5.3.  
5. Executar smoke da secção 5.5.  
6. Explicar ao utilizador o comportamento esperado:
   - **1.º carregamento** após restart do backend: loading longo no TopBar (~15–90 s).  
   - **2.º F5** com backend ainda ligado: rápido (cache “Reutilizando sessão autenticada”).  
7. Se **401** após restart:  
   - `POST http://127.0.0.1:8000/almox/v1/session/reset-erp`  
   - novo `GET /current` ou reload na UI.

### 6.2 O que NÃO é “perda de conexão permanente”

| Situação | Normal? | Ação |
|----------|---------|------|
| Restart do uvicorn → 1ª `/current` lenta | Sim | Aguardar |
| 2ª `/current` rápida com backend ligado | Sim | — |
| 401 com `NotImplementedError` vazio | Não | Reiniciar backend com **venv** + Proactor (secção 5.2) |
| 401 com `Executable doesn't exist` | Não | `playwright install chromium` no venv |
| UI 401 mas curl 200 | Não | `VITE_API_URL`, cache browser, dois uvicorn na 8000 |

---

## 7. Prompt sugerido para o utilizador colar no Antigravity / outra IA

```
Estou no projeto health-ops-almoxarifado (branch release/context-commit-stable).

Antes de qualquer código:
1. Lê docs/AI_SESSION_START_HERE.md
2. Lê docs/AI_OPERATIONS_LOCAL_SERVERS.md
3. Lê docs/OFFICIAL_LOCAL_PORTS.md

Tarefa: [descrever — ex. reiniciar backend+frontend e validar /session/current]

Regras:
- Backend só com backend\.venv\Scripts\python.exe na porta 8000
- Não usar porta 8001
- Parar processos nas portas 8000 e 5173 antes de subir de novo
- Validar com /docs e /almox/v1/session/diagnostics antes de dizer que está pronto
- Responder em PT-BR
```

---

## 8. Mapa de documentação (não reinventar)

| Preciso de… | Documento |
|-------------|-------------|
| Portas e 401 ERP | [OFFICIAL_LOCAL_PORTS.md](./OFFICIAL_LOCAL_PORTS.md) |
| Contexto Vivver / não mexer no motor | [evidence/context-switch/README.md](./evidence/context-switch/README.md) |
| Estado do projeto e próximo foco | [AI_SESSION_START_HERE.md](./AI_SESSION_START_HERE.md) |
| Checklist UI pré-merge | [FRONTEND_BASELINE_PROTOCOL.md](./core-platform/FRONTEND_BASELINE_PROTOCOL.md) |
| Boot detalhado / env | [RELEASE_HANDOFF.md](./evidence/context-switch/RELEASE_HANDOFF.md) |

---

## 9. Registo de validação (opcional)

Quando a IA concluir um ciclo “reiniciar + validar”, pode deixar nota em `docs/evidence/baseline-runs/AAAA-MM-DD/` ou uma linha em [FRONTEND_BASELINE_PROTOCOL.md](./core-platform/FRONTEND_BASELINE_PROTOCOL.md): data, branch, `/current` 1ª e 2ª chamada (tempo + HTTP), observações.

---

*Última revisão: alinhado ao commit com Proactor Windows + `/diagnostics` + `start-backend.ps1`.*
