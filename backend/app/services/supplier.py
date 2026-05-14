import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_, func
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate

class SupplierService:
    @staticmethod
    async def list_suppliers(
        db: AsyncSession, 
        q: str | None = None,
        include_archived: bool = False
    ):
        query = select(Supplier)
        
        # ADR-001: Filter out archived by default
        if not include_archived:
            query = query.where(Supplier.deleted_at.is_(None))
        
        if q:
            # Enhanced search: name, trade name or document (Requirement 10)
            query = query.where(
                or_(
                    Supplier.corporate_name.ilike(f"%{q}%"),
                    Supplier.trade_name.ilike(f"%{q}%"),
                    Supplier.document.ilike(f"%{q}%")
                )
            )
        
        result = await db.execute(query.order_by(Supplier.corporate_name))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(db: AsyncSession, supplier_id: uuid.UUID):
        query = select(Supplier).where(
            Supplier.id == supplier_id,
            Supplier.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, schema: SupplierCreate):
        new_supplier = Supplier(**schema.model_dump())
        db.add(new_supplier)
        await db.commit()
        await db.refresh(new_supplier)
        return new_supplier

    @staticmethod
    async def update(
        db: AsyncSession, 
        supplier_id: uuid.UUID, 
        schema: SupplierUpdate
    ):
        update_data = schema.model_dump(exclude_unset=True)
        if not update_data:
            return await SupplierService.get_by_id(db, supplier_id)

        stmt = (
            update(Supplier)
            .where(
                Supplier.id == supplier_id,
                Supplier.deleted_at.is_(None)
            )
            .values(**update_data)
            .returning(Supplier)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()

    @staticmethod
    async def archive(db: AsyncSession, supplier_id: uuid.UUID):
        # Soft delete semantic (ADR-001)
        stmt = (
            update(Supplier)
            .where(
                Supplier.id == supplier_id,
                Supplier.deleted_at.is_(None)
            )
            .values(deleted_at=func.now())
            .returning(Supplier)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()
