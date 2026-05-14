import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.models.product import Product
from app.models.inventory_movement import InventoryMovement, MovementType
from app.schemas.inventory_movement import MovementCreate
from fastapi import HTTPException

class InventoryMovementService:
    @staticmethod
    async def create_movement(
        db: AsyncSession, 
        product_id: uuid.UUID, 
        type: MovementType, 
        quantity: float, 
        reference_document: str | None = None,
        reason: str | None = None,
        created_by: str = "system"
    ):
        from app.core.context import get_current_tenant_id, get_current_unit_id, sector_id as context_sector_id
        
        tenant_id = get_current_tenant_id()
        unit_id = get_current_unit_id()
        sector_id = context_sector_id.get() # sector_id from context

        if not tenant_id or not unit_id or not sector_id:
            raise HTTPException(
                status_code=400, 
                detail="Operational Context (Tenant, Unit, Sector) is mandatory for inventory movements."
            )

        # 1. Row-level lock on the InventoryBalance (ADR-011)
        # We lock the balance for this specific product/sector
        from app.models.inventory_balance import InventoryBalance
        from sqlalchemy import select
        
        balance_query = select(InventoryBalance).where(
            InventoryBalance.product_id == product_id,
            InventoryBalance.tenant_id == tenant_id,
            InventoryBalance.unit_id == unit_id,
            InventoryBalance.sector_id == sector_id
        ).with_for_update()
        
        result = await db.execute(balance_query)
        inv_balance = result.scalar_one_or_none()
        
        if not inv_balance:
            # Create the balance row if it doesn't exist
            inv_balance = InventoryBalance(
                product_id=product_id,
                tenant_id=tenant_id,
                unit_id=unit_id,
                sector_id=sector_id,
                balance=0.0
            )
            db.add(inv_balance)
            await db.flush()
            # Re-lock
            result = await db.execute(balance_query)
            inv_balance = result.scalar_one()

        # 2. Calculate New Balance
        if type in [MovementType.ENTRY, MovementType.INITIAL_ENTRY]:
            new_balance = float(inv_balance.balance) + quantity
        else: # EXIT or ADJUSTMENT (negative)
            new_balance = float(inv_balance.balance) - quantity
            
        # 3. Stock Validation (Prevention of Negative Stock)
        if new_balance < 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock in sector. Current: {inv_balance.balance}, Requested Exit: {quantity}"
            )
        
        # 4. Record Movement
        movement = InventoryMovement(
            product_id=product_id,
            tenant_id=tenant_id,
            unit_id=unit_id,
            sector_id=sector_id,
            type=type,
            quantity=quantity,
            reference_document=reference_document,
            reason=reason,
            created_by=created_by
        )
        
        # 5. Update Materialized Balance
        inv_balance.balance = new_balance
        
        db.add(movement)
        await db.flush()
        
        return movement

    @staticmethod
    async def list_movements(
        db: AsyncSession, 
        product_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 20
    ):
        base_query = select(InventoryMovement)
        if product_id:
            base_query = base_query.where(InventoryMovement.product_id == product_id)
        
        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        # Get items
        query = base_query.order_by(InventoryMovement.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all(), total
