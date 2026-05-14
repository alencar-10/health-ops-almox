import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_, func
from app.models.manufacturer import Manufacturer
from app.schemas.manufacturer import ManufacturerCreate, ManufacturerUpdate

class ManufacturerService:
    @staticmethod
    async def list_manufacturers(
        db: AsyncSession, 
        q: str | None = None,
        include_archived: bool = False
    ):
        query = select(Manufacturer)
        
        if not include_archived:
            query = query.where(Manufacturer.deleted_at.is_(None))
        
        if q:
            query = query.where(
                or_(
                    Manufacturer.corporate_name.ilike(f"%{q}%"),
                    Manufacturer.trade_name.ilike(f"%{q}%"),
                    Manufacturer.document.ilike(f"%{q}%")
                )
            )
        
        result = await db.execute(query.order_by(Manufacturer.corporate_name))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, manufacturer_id: uuid.UUID):
        query = select(Manufacturer).where(
            Manufacturer.id == manufacturer_id,
            Manufacturer.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, schema: ManufacturerCreate):
        new_manufacturer = Manufacturer(**schema.model_dump())
        db.add(new_manufacturer)
        await db.commit()
        await db.refresh(new_manufacturer)
        return new_manufacturer

    @staticmethod
    async def update(
        db: AsyncSession, 
        manufacturer_id: uuid.UUID, 
        schema: ManufacturerUpdate
    ):
        update_data = schema.model_dump(exclude_unset=True)
        if not update_data:
            return await ManufacturerService.get_by_id(db, manufacturer_id)

        stmt = (
            update(Manufacturer)
            .where(
                Manufacturer.id == manufacturer_id,
                Manufacturer.deleted_at.is_(None)
            )
            .values(**update_data)
            .returning(Manufacturer)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()

    @staticmethod
    async def archive(db: AsyncSession, manufacturer_id: uuid.UUID):
        stmt = (
            update(Manufacturer)
            .where(
                Manufacturer.id == manufacturer_id,
                Manufacturer.deleted_at.is_(None)
            )
            .values(deleted_at=func.now())
            .returning(Manufacturer)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()
