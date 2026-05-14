import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.inventory_movement import InventoryMovement, MovementType
from app.models.inventory_balance import InventoryBalance
from app.core.logging import logger

class InventoryRebuildService:
    """
    Ensures the Materialized Balance matches the Immutable Ledger (ADR-011).
    Source of Truth: InventoryMovement.
    """
    @staticmethod
    async def rebuild_balance(
        db: AsyncSession, 
        product_id: uuid.UUID, 
        sector_id: uuid.UUID
    ):
        logger.info(f"Rebuilding balance for product {product_id} in sector {sector_id}")
        
        # 1. Fetch the balance row (lock it)
        balance_query = select(InventoryBalance).where(
            InventoryBalance.product_id == product_id,
            InventoryBalance.sector_id == sector_id
        ).with_for_update()
        
        result = await db.execute(balance_query)
        inv_balance = result.scalar_one_or_none()
        
        if not inv_balance:
            # This shouldn't happen if movements exist, but we handle it
            logger.warning(f"No balance row found for product {product_id} / sector {sector_id}. Checking movements...")
        
        # 2. Sum all movements (Ledger)
        # Entry/InitialEntry (+) vs Exit/Adjustment (-)
        # Note: We need to handle the signs correctly
        movements_query = select(
            InventoryMovement.type,
            func.sum(InventoryMovement.quantity).label("total")
        ).where(
            InventoryMovement.product_id == product_id,
            InventoryMovement.sector_id == sector_id
        ).group_by(InventoryMovement.type)
        
        results = (await db.execute(movements_query)).all()
        
        new_balance = 0.0
        for row in results:
            if row.type in [MovementType.ENTRY, MovementType.INITIAL_ENTRY]:
                new_balance += float(row.total)
            else: # EXIT or ADJUSTMENT (which we assume was recorded as positive quantity but represents negative change)
                # In our logic, ADJUSTMENT quantity is subtracted.
                new_balance -= float(row.total)

        # 3. Update or Create Balance
        if not inv_balance:
            # Need to find Tenant/Unit for the balance row
            # We can get it from the first movement found
            first_mov_query = select(InventoryMovement).where(
                InventoryMovement.product_id == product_id,
                InventoryMovement.sector_id == sector_id
            ).limit(1)
            first_mov = (await db.execute(first_mov_query)).scalar_one_or_none()
            
            if not first_mov:
                logger.error(f"Cannot rebuild balance: No movements found for product {product_id} in sector {sector_id}")
                return 0.0

            inv_balance = InventoryBalance(
                product_id=product_id,
                tenant_id=first_mov.tenant_id,
                unit_id=first_mov.unit_id,
                sector_id=first_mov.sector_id,
                balance=new_balance
            )
            db.add(inv_balance)
        else:
            inv_balance.balance = new_balance
            
        await db.flush()
        logger.info(f"Balance rebuild successful. New Balance: {new_balance}")
        return new_balance
