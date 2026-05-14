import asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.db.base import Base
from app.models.product import Product
from app.models.manufacturer import Manufacturer
from app.models.active_ingredient import ActiveIngredient
from app.models.supplier import Supplier
from app.models.inbound import InboundSession, InboundItem, InboundStatus, InboundType
from app.models.inventory_balance import InventoryBalance
from app.models.inventory_movement import InventoryMovement
from app.services.inbound.reconciler import InboundReconciler
from app.services.stock.inbound_ledger_service import InboundLedgerService
from app.services.integration.erp_sync_service import ERPSyncService

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/almox_db"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def run_final_lab():
    async with AsyncSessionLocal() as db:
        print("\n--- [LAB] FINAL OPERATIONAL VALIDATION (CYCLE 28) ---\n")
        
        # 1. SETUP: Real Context (Existing IDs)
        tenant_id = uuid.UUID("fb0282be-1b58-40ce-a124-1cf897e1a393")
        unit_id = uuid.UUID("3d14d3ea-52f4-42f7-bfa3-4e1fa1aabd42")
        sector_id = uuid.UUID("4c77f589-b9fb-4707-8f4f-6c7e19eaaca1")
        operator = "admin_reconciler"

        # 2. SEED: Catalog Data (Source of Truth)
        m_ache = Manufacturer(id=uuid.uuid4(), corporate_name="ACHÉ LABORATÓRIOS FARMACÊUTICOS S.A.", external_id="1")
        db.add(m_ache)
        
        p_amox = Product(
            id=uuid.uuid4(), tenant_id=tenant_id, name="AMOXICILINA 500MG COMPRIMIDO", 
            sku=f"AMX-500-{uuid.uuid4().hex[:4]}", ean=f"{uuid.uuid4().hex[:13]}", 
            external_code="101", unit_of_measure="UNIT"
        )
        db.add(p_amox)
        await db.commit()
        print(f"Catalog Seeded: {p_amox.name} | Manufacturer: {m_ache.corporate_name}")

        # 3. INBOUND: Simulating XML Staging (Raw State)
        session = InboundSession(
            tenant_id=tenant_id, unit_id=unit_id, sector_id=sector_id,
            type=InboundType.XML_NFE, status=InboundStatus.NEW,
            external_reference="NF-2024-ABC"
        )
        db.add(session)
        await db.flush()

        item_xml = InboundItem(
            session_id=session.id,
            raw_product_name="AMOXICILINA 500MG", # Raw name from XML
            raw_manufacturer_name="ACHE LAB",      # Divergent name
            raw_gtin="789123456001",
            batch_number="B-99-TEST",
            expiry_date=datetime(2027, 12, 31),
            quantity_received=100.0,
            unit_price=15.50
        )
        db.add(item_xml)
        await db.commit()
        print(f"Inbound Staged: {item_xml.raw_product_name} (Status: NEW)")

        # 4. RECONCILIATION: Weighted Matching (ADR-014)
        reconciler = InboundReconciler(db)
        # Search using the structural engine
        suggestions = await reconciler.fuzzy.search_products(item_xml)
        print(f"IA Suggestions Found: {len(suggestions)}")
        for s in suggestions:
            print(f"  > [{s['score']}%] {s['label']} (Reason: {s['metadata'].get('reason', 'Weighted')})")

        # 5. HUMAN DECISION: Confirm Match (with Audit History)
        best = suggestions[0]
        await reconciler.reconcile_item(
            item_xml.id, 
            product_id=best['id'], 
            manufacturer_id=m_ache.id,
            score=best['score'],
            metadata=best['metadata']
        )
        
        # Verify History & Warnings
        await db.refresh(item_xml)
        print(f"Item Reconciled: is_matched={item_xml.is_matched} | Score: {item_xml.match_score}")
        if item_xml.match_metadata and "warnings" in item_xml.match_metadata:
            print(f"Warnings Detected: {item_xml.match_metadata['warnings']}")

        # 6. UNDO SIMULATION (Causal Reversal)
        print("Human error detected! Undoing reconciliation...")
        await reconciler.undo_reconciliation(item_xml.id)
        await db.refresh(item_xml)
        print(f"State after Undo: is_matched={item_xml.is_matched} | History Size: {len(item_xml.reconciliation_history)}")

        # Re-apply correctly
        await reconciler.reconcile_item(item_xml.id, product_id=p_amox.id, manufacturer_id=m_ache.id, score=100)

        # 7. LEDGER COMMITMENT (Operational Authority)
        ledger = InboundLedgerService(db)
        await ledger.commit_session(session.id, created_by=operator)
        print(f"Session Committed to Ledger (Status: {session.status})")

        # 8. DRIFT VALIDATION (ADR-014)
        balance_res = await db.execute(select(InventoryBalance).where(InventoryBalance.product_id == p_amox.id))
        balance = balance_res.scalar_one()
        print(f"Operational Balance: {balance.balance} | ERP Synced Balance: {balance.erp_synced_balance}")
        print(f"Current Operational Drift: {balance.balance - balance.erp_synced_balance} items")

        # 9. ERP SYNC (Side Effect Resolution)
        sync_service = ERPSyncService(db)
        await sync_service.sync_session(session.id)
        await db.refresh(balance)
        print(f"Vivver Sync Completed (Status: {session.status})")
        print(f"Drift Resolved! New ERP Synced Balance: {balance.erp_synced_balance}")

        print("\n--- [LAB] FINAL VALIDATION SUCCESSFUL ---\n")

if __name__ == "__main__":
    asyncio.run(run_final_lab())
