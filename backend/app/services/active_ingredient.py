import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_, func
from app.models.active_ingredient import ActiveIngredient
from app.schemas.active_ingredient import ActiveIngredientCreate, ActiveIngredientUpdate
from datetime import datetime, timezone

class ActiveIngredientService:
    @staticmethod
    async def get_active_ingredients(
        db: AsyncSession, 
        q: str | None = None,
        include_archived: bool = False
    ):
        query = select(ActiveIngredient)
        
        # Filter out archived by default (Requirement 5)
        if not include_archived:
            query = query.where(ActiveIngredient.deleted_at.is_(None))
        
        # Simple search (Requirement 7)
        if q:
            query = query.where(
                or_(
                    ActiveIngredient.name.ilike(f"%{q}%"),
                    ActiveIngredient.description.ilike(f"%{q}%")
                )
            )
        
        result = await db.execute(query.order_by(ActiveIngredient.name))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, ingredient_id: uuid.UUID):
        query = select(ActiveIngredient).where(
            ActiveIngredient.id == ingredient_id,
            ActiveIngredient.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, schema: ActiveIngredientCreate):
        new_ingredient = ActiveIngredient(**schema.model_dump())
        db.add(new_ingredient)
        await db.commit()
        await db.refresh(new_ingredient)
        return new_ingredient

    @staticmethod
    async def update(
        db: AsyncSession, 
        ingredient_id: uuid.UUID, 
        schema: ActiveIngredientUpdate
    ):
        # We use a select then update or a direct update? 
        # Direct update to respect the database-level trigger for updated_at
        update_data = schema.model_dump(exclude_unset=True)
        if not update_data:
            return await ActiveIngredientService.get_by_id(db, ingredient_id)

        stmt = (
            update(ActiveIngredient)
            .where(
                ActiveIngredient.id == ingredient_id,
                ActiveIngredient.deleted_at.is_(None)
            )
            .values(**update_data)
            .returning(ActiveIngredient)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()

    @staticmethod
    async def archive(db: AsyncSession, ingredient_id: uuid.UUID):
        # Soft delete semantic (Requirement 3)
        stmt = (
            update(ActiveIngredient)
            .where(
                ActiveIngredient.id == ingredient_id,
                ActiveIngredient.deleted_at.is_(None)
            )
            .values(deleted_at=func.now())
            .returning(ActiveIngredient)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()
