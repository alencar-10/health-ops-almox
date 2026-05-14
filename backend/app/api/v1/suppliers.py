import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.supplier import (
    SupplierRead, 
    SupplierCreate, 
    SupplierUpdate
)
from app.schemas.active_ingredient import StandardResponse
from app.services.supplier import SupplierService
from typing import List

router = APIRouter()

@router.get("/", response_model=StandardResponse[List[SupplierRead]])
async def list_suppliers(
    q: str | None = Query(None, description="Search by corporate name, trade name or document"),
    db: AsyncSession = Depends(get_db)
):
    suppliers = await SupplierService.list_suppliers(db, q=q)
    return {"data": suppliers, "message": "success"}

@router.post("/", response_model=StandardResponse[SupplierRead], status_code=201)
async def create_supplier(
    payload: SupplierCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        supplier = await SupplierService.create(db, payload)
        return {"data": supplier, "message": "created successfully"}
    except Exception as e:
        if "unique constraint" in str(e).lower():
            # ADR-001/002: Document already exists (even if archived)
            raise HTTPException(status_code=400, detail="Document already exists (check archives)")
        raise e

@router.get("/{supplier_id}", response_model=StandardResponse[SupplierRead])
async def get_supplier(
    supplier_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    supplier = await SupplierService.get_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"data": supplier, "message": "success"}

@router.patch("/{supplier_id}", response_model=StandardResponse[SupplierRead])
async def update_supplier(
    supplier_id: uuid.UUID,
    payload: SupplierUpdate,
    db: AsyncSession = Depends(get_db)
):
    supplier = await SupplierService.update(db, supplier_id, payload)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"data": supplier, "message": "updated successfully"}

@router.delete("/{supplier_id}", response_model=StandardResponse[SupplierRead])
async def archive_supplier(
    supplier_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    supplier = await SupplierService.archive(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"data": supplier, "message": "archived successfully"}
