import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.inventory_movement import (
    MovementRead, 
    MovementCreate
)
from app.schemas.active_ingredient import StandardResponse
from app.services.inventory_movement import InventoryMovementService
from typing import List

router = APIRouter()

from app.schemas.common import PaginationParams, PaginatedResponse
import math

@router.get("/", response_model=PaginatedResponse[MovementRead])
async def list_movements(
    params: PaginationParams = Depends(),
    product_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    skip = (params.page - 1) * params.limit
    movements, total = await InventoryMovementService.list_movements(
        db, product_id=product_id, skip=skip, limit=params.limit
    )
    
    return {
        "items": movements,
        "total": total,
        "page": params.page,
        "limit": params.limit,
        "total_pages": math.ceil(total / params.limit) if total > 0 else 0,
        "message": "success"
    }

@router.post("/", response_model=StandardResponse[MovementRead], status_code=201)
async def create_movement(
    payload: MovementCreate,
    db: AsyncSession = Depends(get_db)
):
    movement = await InventoryMovementService.create_movement(db, **payload.model_dump())
    await db.commit()
    await db.refresh(movement)
    return {"data": movement, "message": "movement recorded successfully"}

# NO PATCH or DELETE routes (ADR-004: Ledger Immutability)
