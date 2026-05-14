import asyncio
import uuid
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Mocking app structure
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import AsyncSessionLocal
from app.models.product import Product
from app.models.active_ingredient import ActiveIngredient # Fix mapping
from app.models.manufacturer import Manufacturer
from app.models.supplier import Supplier
from app.models.organization import Tenant, Unit, Sector
from app.models.inbound import InboundSession, InboundItem, InboundStatus, InboundType
from app.models.inventory_balance import InventoryBalance
from app.models.inventory_movement import InventoryMovement, MovementType
from app.services.inbound.reconciler import InboundReconciler
from app.services.stock.inbound_ledger_service import InboundLedgerService

async def run_resilience_lab():
    print("\n--- [LAB] OPERATIONAL RESILIENCE VALIDATION (ADR-015) ---")
    
    async with AsyncSessionLocal() as db:
        # 1. SETUP: Identical IDs from DB for consistency
        tenant_id = uuid.UUID("fb0282be-1b58-40ce-a124-1cf897e1a393")
        unit_id = uuid.UUID("3d14d3ea-52f4-42f7-bfa3-4e1fa1aabd42")
        sector_id = uuid.UUID("4c77f589-b9fb-4707-8f4f-6c7e19eaaca1")
        operator = "LAB_OPERATOR_015"

        # 2. SEED: Create a Product
        ean = f"RESI-{uuid.uuid4().hex[:8]}"
        product = Product(
            id=uuid.uuid4(), tenant_id=tenant_id, name="RESILIENCE TEST DRUG", 
            sku=f"SKU-{uuid.uuid4().hex[:4]}", ean=ean, external_code="RESI-01",
            unit_of_measure="UNIT"
        )
        db.add(product)
        await db.commit()

        # 3. OPERATION: Stage, Match and POST
        session = InboundSession(
            tenant_id=tenant_id, unit_id=unit_id, sector_id=sector_id,
            type=InboundType.MANUAL, status=InboundStatus.NEW,
            external_reference="DOC-RESILIENCE"
        )
        db.add(session)
        await db.flush()

        item = InboundItem(
            session_id=session.id, raw_product_name="RESILIENCE TEST DRUG",
            raw_gtin=ean, batch_number="LOT-2024", 
            expiry_date=datetime.now() + timedelta(days=365),
            quantity_received=50.0, is_matched=True, product_id=product.id,
            match_score=100.0
        )
        db.add(item)
        await db.commit()

        # 4. COMMIT TO LEDGER (Immutable Point)
        ledger = InboundLedgerService(db)
        await ledger.commit_session(session.id, created_by=operator)
        print(f"Session POSTED. Current Status: {session.status}")

        # Verify Initial Movement
        mov_res = await db.execute(select(InventoryMovement).where(InventoryMovement.product_id == product.id))
        movements = mov_res.scalars().all()
        print(f"Movements after POST: {[m.type for m in movements]} (Count: {len(movements)})")

        # 5. FORENSIC UNDO (The Storno)
        reconciler = InboundReconciler(db)
        print("Executing Forensic Undo on POSTED session...")
        await reconciler.undo_reconciliation(item.id, reversed_by=operator, reason="Lab Reversal Test")
        
        # 6. VERIFICATION
        # A. Session status should revert to CONFIRMED
        await db.refresh(session)
        print(f"Session Status after Undo: {session.status}")

        # B. Reversal Movement must exist
        mov_res = await db.execute(select(InventoryMovement).where(InventoryMovement.product_id == product.id))
        all_movements = mov_res.scalars().all()
        print(f"Movements after Undo: {[m.type for m in all_movements]} (Count: {len(all_movements)})")
        
        reversal = next((m for m in all_movements if m.type == MovementType.REVERSAL), None)
        if reversal and reversal.quantity == -50.0:
            print("SUCCESS: Compensatory Movement (Storno) found with correct negative quantity.")
        else:
            print("FAILURE: Compensatory Movement missing or incorrect.")

        # C. Balance should be 0
        bal_res = await db.execute(select(InventoryBalance).where(InventoryBalance.product_id == product.id))
        balance = bal_res.scalar_one_or_none()
        print(f"Final Balance: {balance.balance if balance else 'N/A'}")

        if balance and float(balance.balance) == 0.0:
            print("--- [LAB] RESILIENCE VALIDATION SUCCESSFUL ---")
        else:
            print("--- [LAB] RESILIENCE VALIDATION FAILED ---")

if __name__ == "__main__":
    asyncio.run(run_resilience_lab())
