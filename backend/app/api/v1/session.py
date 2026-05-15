import asyncio
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.core.auth.factory import AuthEngineFactory
from app.core.auth.operations import ContextOperation, OperationStatus, OperationStore
from app.core.config import settings
from app.schemas.common import StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter()


async def _resolve_sector_id(engine, unit_id: str, sector_id: Optional[str]) -> tuple[str, str]:
    """
    Resolve setor alvo. Só auto-seleciona se houver exatamente um setor (não é heurística de 'primeiro').
    """
    # codsetor=0 é válido no Vivver (ex.: ATENDIMENTO) — não tratar "0" como ausente
    if sector_id is not None and str(sector_id).strip() not in ("", "AUTO_RESOLVE"):
        return str(sector_id).strip(), "EXPLICIT"

    sectors = await engine.list_available_sectors(unit_id)
    if not sectors:
        raise ValueError("NO_SECTORS_AVAILABLE")
    if len(sectors) == 1:
        return str(sectors[0]["key"]), "SINGLE_OPTION"
    raise ValueError("MULTIPLE_SECTORS")

@router.get("/current", response_model=StandardResponse[dict])
async def get_real_session_context():
    """
    Vertical Slice: Fetches the real operational context from the Vivver Auth Engine.
    """
    try:
        engine = AuthEngineFactory.get_engine()
        # In a real app, we'd use the user's stored credentials or a session token.
        # For the Vertical Slice, we use the system credentials from settings.
        if hasattr(engine, "get_operational_context"):
            context = await engine.get_operational_context()
        else:
            context = await engine.login(
                username=settings.VIVVER_USER,
                password=settings.VIVVER_PASS,
                tenant_id=settings.VITE_MUNICIPALITY_ID,
            )
        
        if not context:
            raise HTTPException(status_code=401, detail="Failed to resolve real ERP context.")
            
        return {
            "data": {
                "prefecture": {
                    "id": context.tenant_id,
                    "name": context.prefecture_name
                },
                "unit": {
                    "id": context.unit_id,
                    "name": context.unit_name
                },
                "sector": {
                    "id": context.sector_id,
                    "name": context.sector_name
                },
                "user": {
                    "id": context.operator_id,
                    "name": context.operator_name,
                    "role": "Gestor"
                },
                "isValid": True
            },
            "message": "Real ERP context resolved successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-units", response_model=StandardResponse[list])
async def list_available_units():
    """
    Exposes the Discovery Engine to the frontend.
    """
    engine = AuthEngineFactory.get_engine()
    units = await engine.list_available_units()
    return {"data": units, "message": "Units discovered via XHR."}

@router.get("/available-sectors", response_model=StandardResponse[list])
async def list_available_sectors(unit_id: str):
    """Setores Vivver disponíveis para a unidade (descoberta real)."""
    engine = AuthEngineFactory.get_engine()
    sectors = await engine.list_available_sectors(unit_id)
    return {"data": sectors, "message": f"{len(sectors)} setores descobertos."}


async def _run_switch_task(op_id: uuid.UUID, u_id: str, s_id: Optional[str]) -> None:
    """Executa a manobra fora do request (asyncio task — BackgroundTasks falha com async+Playwright)."""
    try:
        engine = AuthEngineFactory.get_engine()
        OperationStore.update(
            op_id,
            status=OperationStatus.SWITCHING,
            message="Conectando e aplicando unidade/setor no ERP...",
            progress=30,
        )
        resolved_sector, resolution = await _resolve_sector_id(engine, u_id, s_id)
        OperationStore.update(
            op_id,
            message=f"Setor resolvido ({resolution}): {resolved_sector}",
            progress=40,
            metadata={"sector_resolution": resolution, "sector_id": resolved_sector},
        )
        ctx = await engine.switch_context(
            unit_id=u_id,
            sector_id=resolved_sector,
            operation_id=op_id,
        )
        if ctx is None:
            op = OperationStore.get(op_id)
            if op and op.status not in (
                OperationStatus.FAILED,
                OperationStatus.COMPLETED,
            ):
                OperationStore.update(
                    op_id,
                    status=OperationStatus.FAILED,
                    error="Manobra rejeitada pelo ERP.",
                    message="Troca não persistida no Vivver.",
                )
    except ValueError as exc:
        err = str(exc)
        if err == "MULTIPLE_SECTORS":
            sectors = await AuthEngineFactory.get_engine().list_available_sectors(u_id)
            OperationStore.update(
                op_id,
                status=OperationStatus.MULTIPLE_CHOICES_REQUIRED,
                error="Selecione o setor explicitamente.",
                message="Múltiplos setores disponíveis — escolha no menu SETOR.",
                metadata={"sectors": sectors, "unit_id": u_id},
            )
        else:
            OperationStore.update(
                op_id,
                status=OperationStatus.FAILED,
                error=err,
                message="Falha ao resolver setor.",
            )
    except Exception as exc:
        logger.exception("Context switch task failed")
        OperationStore.update(
            op_id,
            status=OperationStatus.FAILED,
            error=str(exc),
            message="Erro inesperado na manobra.",
        )


@router.post("/switch")
async def switch_real_context(
    unit_id: str,
    sector_id: Optional[str] = None,
):
    """
    Executa a troca de contexto de forma síncrona (30–90s na 1ª vez).
    Retorna a operação já no estado terminal — evita background task que não roda no Windows.
    """
    operation = OperationStore.create(unit_id, sector_id)

    OperationStore.update(
        operation.id,
        status=OperationStatus.NAVIGATING,
        message="Preparando manobra no Vivver ERP...",
        progress=10,
    )

    logger.info("Switch start op=%s unit=%s sector=%s", operation.id, unit_id, sector_id)
    await _run_switch_task(operation.id, unit_id, sector_id)

    final = OperationStore.get(operation.id)
    if not final:
        raise HTTPException(status_code=500, detail="Operação não encontrada após switch.")

    snap = (final.metadata or {}).get("snapshot_after") or {}
    return {
        "data": {
            "operation_id": str(final.id),
            "status": final.status,
            "message": final.message,
            "error": final.error,
            "metadata": final.metadata,
            "target_unit_id": final.target_unit_id,
            "target_sector_id": final.target_sector_id,
            "unit_name": snap.get("unit"),
            "sector_name": snap.get("sector"),
        },
        "message": final.message,
    }

@router.get("/operations/{op_id}", response_model=StandardResponse[ContextOperation])
async def get_operation_status(op_id: uuid.UUID):
    """
    Polling endpoint for context switch operations.
    """
    operation = OperationStore.get(op_id)
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found.")
    return {"data": operation, "message": f"Status: {operation.status}"}
