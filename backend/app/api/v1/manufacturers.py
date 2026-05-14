import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.manufacturer import (
    ManufacturerRead, 
    ManufacturerCreate, 
    ManufacturerUpdate
)
from app.schemas.common import StandardResponse
from app.services.manufacturer import ManufacturerService
from typing import List

router = APIRouter()

@router.get("/", response_model=StandardResponse[List[ManufacturerRead]])
async def list_manufacturers(
    q: str | None = Query(None, description="Search by corporate name, trade name or document"),
    db: AsyncSession = Depends(get_db)
):
    manufacturers = await ManufacturerService.list_manufacturers(db, q=q)
    return {"data": manufacturers, "message": "success"}

@router.post("/", response_model=StandardResponse[ManufacturerRead], status_code=201)
async def create_manufacturer(
    payload: ManufacturerCreate,
    db: AsyncSession = Depends(get_db)
):
    # Note: Unique constraint on document will be handled by DB and raise IntegrityError
    # We could catch it here or in a global exception handler.
    try:
        manufacturer = await ManufacturerService.create(db, payload)
        return {"data": manufacturer, "message": "created successfully"}
    except Exception as e:
        if "unique constraint" in str(e).lower():
            raise HTTPException(status_code=400, detail="Document already exists")
        raise e

@router.get("/{manufacturer_id}", response_model=StandardResponse[ManufacturerRead])
async def get_manufacturer(
    manufacturer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    manufacturer = await ManufacturerService.get_by_id(db, manufacturer_id)
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return {"data": manufacturer, "message": "success"}

@router.patch("/{manufacturer_id}", response_model=StandardResponse[ManufacturerRead])
async def update_manufacturer(
    manufacturer_id: uuid.UUID,
    payload: ManufacturerUpdate,
    db: AsyncSession = Depends(get_db)
):
    manufacturer = await ManufacturerService.update(db, manufacturer_id, payload)
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return {"data": manufacturer, "message": "updated successfully"}

@router.delete("/{manufacturer_id}", response_model=StandardResponse[ManufacturerRead])
async def archive_manufacturer(
    manufacturer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    manufacturer = await ManufacturerService.archive(db, manufacturer_id)
    if not manufacturer:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return {"data": manufacturer, "message": "archived successfully"}
