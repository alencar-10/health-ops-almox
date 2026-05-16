# Arranque canónico do backend (porta 8000) — ver docs/OFFICIAL_LOCAL_PORTS.md
$ErrorActionPreference = "Stop"
$BackendRoot = Split-Path -Parent $PSScriptRoot
Set-Location $BackendRoot

$Python = Join-Path $BackendRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error "venv não encontrado em $Python — crie o venv em backend/ primeiro."
}

Write-Host "Python: $Python"
& $Python -c "from app.core.asyncio_windows import ensure_windows_proactor_event_loop_policy; print('asyncio:', ensure_windows_proactor_event_loop_policy())"

Write-Host "Iniciando uvicorn em http://127.0.0.1:8000 ..."
& $Python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
