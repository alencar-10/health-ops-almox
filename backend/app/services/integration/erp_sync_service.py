import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.inbound import InboundSession, InboundStatus
from app.models.inventory_balance import InventoryBalance

class ERPSyncService:
    """
    Orchestrates the synchronization between HealthOps Ledger and Vivver ERP (Cycle 28).
    Tracks 'Operational Drift' by updating erp_synced_balance (ADR-014).
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_session(self, session_id: uuid.UUID) -> bool:
        """
        Pushes a CONFIRMED session to Vivver.
        If success, updates erp_synced_balance on all items to match local balance.
        """
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(InboundSession)
            .options(selectinload(InboundSession.items))
            .where(InboundSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session: return False
        
        # 1. Simulate Vivver API Call
        # success = await vivver_client.push(session)
        success = True # Mock success
        
        if success:
            # 2. Reconcile Drift with Watermark (ADR-015)
            from app.models.inventory_movement import InventoryMovement
            for item in session.items:
                # Find the most recent movement for this item commit
                movement_res = await self.db.execute(
                    select(InventoryMovement).where(
                        InventoryMovement.product_id == item.product_id,
                        InventoryMovement.batch_number == item.batch_number,
                        InventoryMovement.tenant_id == session.tenant_id,
                        InventoryMovement.unit_id == session.unit_id
                    ).order_by(InventoryMovement.created_at.desc()).limit(1)
                )
                movement = movement_res.scalar_one_or_none()
                
                balance_result = await self.db.execute(
                    select(InventoryBalance).where(
                        InventoryBalance.product_id == item.product_id,
                        InventoryBalance.unit_id == session.unit_id,
                        InventoryBalance.sector_id == session.sector_id,
                        InventoryBalance.batch_number == item.batch_number
                    )
                )
                balance = balance_result.scalar_one_or_none()
                if balance:
                    balance.erp_synced_balance = balance.balance # Drift resolved
                    if movement:
                        balance.last_synced_movement_id = movement.id # Watermark updated

            session.status = InboundStatus.ERP_SYNCED
            await self.db.commit()
            return True
        else:
            session.status = InboundStatus.FAILED
            await self.db.commit()
            return False
