import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_, func
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

class ProductService:
    @staticmethod
    async def list_products(
        db: AsyncSession, 
        q: str | None = None,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 20
    ):
        from app.core.context import get_current_tenant_id
        tenant_id = get_current_tenant_id()
        
        base_query = select(Product)
        
        # Implicit Scoping (ADR-008)
        if tenant_id:
            base_query = base_query.where(Product.tenant_id == tenant_id)
        
        if not include_archived:
            base_query = base_query.where(Product.deleted_at.is_(None))
        
        if q:
            base_query = base_query.where(
                or_(
                    Product.sku.ilike(f"%{q}%"),
                    Product.ean.ilike(f"%{q}%"),
                    Product.name.ilike(f"%{q}%")
                )
            )
        
        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        # Get items with pagination
        query = base_query.order_by(Product.name).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all(), total

    @staticmethod
    async def get_by_id(db: AsyncSession, product_id: uuid.UUID):
        query = select(Product).where(
            Product.id == product_id,
            Product.deleted_at.is_(None)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, schema: ProductCreate):
        from app.services.code_generator import CodeGeneratorService # Note: Need to update this import too
        from app.core.context import get_current_tenant_id, get_current_unit_id
        
        tenant_id = get_current_tenant_id()
        unit_id = get_current_unit_id()

        # 1. Generate Internal Code if tenant context is available (ADR-009)
        internal_code = None
        if tenant_id:
            from app.core.services.code_generator import CodeGeneratorService # Fixed import
            internal_code = await CodeGeneratorService.get_next_code(
                db, tenant_id=tenant_id, entity_type="product"
            )
        
        # 2. Create Product
        new_product = Product(
            **schema.model_dump(),
            tenant_id=tenant_id,
            unit_id=unit_id,
            internal_code=internal_code
        )
        db.add(new_product)
        await db.flush()
        return new_product

    @staticmethod
    async def update(
        db: AsyncSession, 
        product_id: uuid.UUID, 
        schema: ProductUpdate
    ):
        # Note: stock_current is NOT in ProductUpdate schema (ADR-003)
        update_data = schema.model_dump(exclude_unset=True)
        if not update_data:
            return await ProductService.get_by_id(db, product_id)

        stmt = (
            update(Product)
            .where(
                Product.id == product_id,
                Product.deleted_at.is_(None)
            )
            .values(**update_data)
            .returning(Product)
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.scalar_one_or_none()

    @staticmethod
    async def archive(db: AsyncSession, product_id: uuid.UUID):
        stmt = (
            update(Product)
            .where(
                Product.id == product_id,
                Product.deleted_at.is_(None)
            )
            .values(deleted_at=func.now())
            .returning(Product)
        )
        result = await db.execute(stmt)
        await db.flush()
        return result.scalar_one_or_none()
