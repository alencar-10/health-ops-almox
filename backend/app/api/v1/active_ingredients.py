import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.active_ingredient import (
    ActiveIngredientRead, 
    ActiveIngredientCreate, 
    ActiveIngredientUpdate,
    StandardResponse
)
from app.services.active_ingredient import ActiveIngredientService
from typing import List

router = APIRouter()

@router.get("/", response_model=StandardResponse[List[ActiveIngredientRead]])
async def list_active_ingredients(
    q: str | None = Query(None, description="Search by name or description"),
    db: AsyncSession = Depends(get_db)
):
    ingredients = await ActiveIngredientService.get_active_ingredients(db, q=q)
    return {"data": ingredients, "message": "success"}

@router.post("/", response_model=StandardResponse[ActiveIngredientRead], status_code=201)
async def create_active_ingredient(
    payload: ActiveIngredientCreate,
    db: AsyncSession = Depends(get_db)
):
    # Check for existing name to avoid unique constraint error
    # (Simple check here, or handle exception in service)
    ingredient = await ActiveIngredientService.create(db, payload)
    return {"data": ingredient, "message": "created successfully"}

@router.get("/{ingredient_id}", response_model=StandardResponse[ActiveIngredientRead])
async def get_active_ingredient(
    ingredient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    ingredient = await ActiveIngredientService.get_by_id(db, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Active ingredient not found")
    return {"data": ingredient, "message": "success"}

@router.patch("/{ingredient_id}", response_model=StandardResponse[ActiveIngredientRead])
async def update_active_ingredient(
    ingredient_id: uuid.UUID,
    payload: ActiveIngredientUpdate,
    db: AsyncSession = Depends(get_db)
):
    ingredient = await ActiveIngredientService.update(db, ingredient_id, payload)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Active ingredient not found")
    return {"data": ingredient, "message": "updated successfully"}

@router.delete("/{ingredient_id}", response_model=StandardResponse[ActiveIngredientRead])
async def archive_active_ingredient(
    ingredient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    # Requirement 3: deactivate/archive instead of delete
    ingredient = await ActiveIngredientService.archive(db, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Active ingredient not found")
    return {"data": ingredient, "message": "archived successfully"}
