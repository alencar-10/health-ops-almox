import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.product import (
    ProductRead, 
    ProductCreate, 
    ProductUpdate
)
from app.schemas.common import PaginationParams, PaginatedResponse, StandardResponse
from app.services.product import ProductService
import math

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[ProductRead])
async def list_products(
    params: PaginationParams = Depends(),
    q: str | None = Query(None, description="Search by SKU, EAN or name"),
    db: AsyncSession = Depends(get_db)
):
    skip = (params.page - 1) * params.limit
    products, total = await ProductService.list_products(
        db, q=q, skip=skip, limit=params.limit
    )
    
    return {
        "items": products,
        "total": total,
        "page": params.page,
        "limit": params.limit,
        "total_pages": math.ceil(total / params.limit) if total > 0 else 0,
        "message": "success"
    }

@router.post("/", response_model=StandardResponse[ProductRead], status_code=201)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        product = await ProductService.create(db, payload)
        await db.commit()
        await db.refresh(product)
        return {"data": product, "message": "created successfully"}
    except Exception as e:
        if "unique constraint" in str(e).lower():
            if "sku" in str(e).lower():
                raise HTTPException(status_code=400, detail="SKU already exists")
            if "ean" in str(e).lower():
                raise HTTPException(status_code=400, detail="EAN already exists")
        raise e

@router.get("/{product_id}", response_model=StandardResponse[ProductRead])
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    product = await ProductService.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"data": product, "message": "success"}

@router.patch("/{product_id}", response_model=StandardResponse[ProductRead])
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    product = await ProductService.update(db, product_id, payload)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.commit()
    await db.refresh(product)
    return {"data": product, "message": "updated successfully"}

@router.delete("/{product_id}", response_model=StandardResponse[ProductRead])
async def archive_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    product = await ProductService.archive(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.commit()
    await db.refresh(product)
    return {"data": product, "message": "archived successfully"}
