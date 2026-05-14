import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.inbound import InboundSession, InboundItem, InboundStatus
from app.models.inventory_balance import InventoryBalance
from app.models.inventory_movement import InventoryMovement, MovementType

from app.models.batch import BatchLot

class InboundLedgerService:
    """
    Finalizes an Inbound Session by committing it to the local Ledger (Cycle 28).
    Implements the batch-scoped balance updates (ADR-012) and BatchLot management.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def reverse_item_commitment(self, item_id: uuid.UUID, reversed_by: str, reason: str) -> bool:
        """
        Forensic Reversal (Storno Pattern - ADR-015).
        Creates a compensatory movement to neutralize a previously posted item.
        """
        result = await self.db.execute(
            select(InboundItem).join(InboundSession).where(InboundItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item or not item.product_id: return False
        
        session = item.session
        
        # 1. Create Compensatory Movement (Negative Quantity)
        storno = InventoryMovement(
            tenant_id=session.tenant_id,
            unit_id=session.unit_id,
            sector_id=session.sector_id,
            product_id=item.product_id,
            batch_number=item.batch_number,
            expiry_date=item.expiry_date,
            type=MovementType.REVERSAL,
            quantity=-item.quantity_received, # Neutralize
            reason=f"STORNO: {reason}",
            reference_document=f"STORNO-{session.external_reference}" if session.external_reference else "STORNO-MANUAL",
            created_by=reversed_by
        )
        self.db.add(storno)
        
        # 2. Update Balance
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
            balance.balance = float(balance.balance) - float(item.quantity_received)
            
        await self.db.commit()
        return True

    async def commit_session(self, session_id: uuid.UUID, created_by: str) -> InboundSession:
        result = await self.db.execute(
            select(InboundSession).where(InboundSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session: raise ValueError("Session not found")
        if session.status == InboundStatus.POSTED: return session
            
        item_result = await self.db.execute(
            select(InboundItem).where(InboundItem.session_id == session.id)
        )
        items = item_result.scalars().all()
        
        for item in items:
            if not item.is_matched:
                raise ValueError(f"Item '{item.raw_product_name}' is not reconciled yet.")

        # 3. Process Each Item (Transactional Batch & Ledger Update)
        for item in items:
            # A. Resolve or Create BatchLot Aggregate (Cycle 28)
            batch_result = await self.db.execute(
                select(BatchLot).where(
                    BatchLot.product_id == item.product_id,
                    BatchLot.batch_number == item.batch_number
                )
            )
            batch = batch_result.scalar_one_or_none()
            if not batch:
                batch = BatchLot(
                    tenant_id=session.tenant_id,
                    product_id=item.product_id,
                    manufacturer_id=item.manufacturer_id,
                    batch_number=item.batch_number,
                    expiry_date=item.expiry_date
                )
                self.db.add(batch)
                await self.db.flush() # Ensure ID is generated if needed

            # B. Create Movement
            movement = InventoryMovement(
                tenant_id=session.tenant_id,
                unit_id=session.unit_id,
                sector_id=session.sector_id,
                product_id=item.product_id,
                batch_number=item.batch_number,
                expiry_date=item.expiry_date,
                type=MovementType.ENTRY,
                quantity=item.quantity_received,
                reference_document=f"REF-{session.external_reference}" if session.external_reference else "MANUAL",
                created_by=created_by
            )
            self.db.add(movement)

            # C. Update Balance (Batch-Scoped)
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
                balance.balance = float(balance.balance) + float(item.quantity_received)
                # Keep expiry updated in balance for FEFO sorting
                balance.expiry_date = item.expiry_date
            else:
                balance = InventoryBalance(
                    tenant_id=session.tenant_id,
                    unit_id=session.unit_id,
                    sector_id=session.sector_id,
                    product_id=item.product_id,
                    batch_number=item.batch_number,
                    expiry_date=item.expiry_date,
                    balance=item.quantity_received
                )
                self.db.add(balance)

        # 4. Finalize Session (Local Commit)
        session.status = InboundStatus.POSTED
        # TODO: Trigger Vivver Sync Async here
        
        await self.db.commit()
        return session
