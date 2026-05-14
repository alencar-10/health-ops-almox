from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.inbound import InboundSession, InboundItem, InboundStatus
from app.schemas.inbound import InboundSessionSchema, InboundItemSchema, InboundReconcileRequest
from app.services.inbound.reconciler import InboundReconciler
from app.services.stock.inbound_ledger_service import InboundLedgerService

router = APIRouter()

@router.get("/", response_model=List[InboundSessionSchema])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List all inbound sessions.
    """
    result = await db.execute(select(InboundSession).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{session_id}", response_model=InboundSessionSchema)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get session details with items.
    """
    result = await db.execute(
        select(InboundSession).where(InboundSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.put("/items/{item_id}/reconcile", response_model=InboundItemSchema)
async def reconcile_item(
    item_id: UUID,
    request: InboundReconcileRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Reconcile a single item (Human confirmation).
    """
    reconciler = InboundReconciler(db)
    item = await reconciler.reconcile_item(
        item_id, 
        product_id=request.product_id, 
        manufacturer_id=request.manufacturer_id,
        score=request.score,
        metadata=request.metadata
    )
    return item

@router.delete("/items/{item_id}/reconcile", response_model=InboundItemSchema)
async def undo_reconcile_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Undo reconciliation for a single item.
    """
    reconciler = InboundReconciler(db)
    item = await reconciler.undo_reconciliation(item_id)
    return item

@router.post("/{session_id}/confirm", response_model=InboundSessionSchema)
async def confirm_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Finalize session and commit to ledger.
    """
    ledger_service = InboundLedgerService(db)
    # FIXME: Use current user instead of "web_operator"
    session = await ledger_service.commit_session(session_id, created_by="web_operator")
    return session
