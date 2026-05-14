import asyncio
import uuid
import sys
from sqlalchemy import select
from app.db.base import Base
from app.db.session import AsyncSessionLocal
from app.services.inbound.stock_entry_service import StockEntryService
from app.services.inbound.reconciler import InboundReconciler, FuzzyReconciler
from app.services.stock.inbound_ledger_service import InboundLedgerService
from app.models.organization import Tenant, Unit, Sector
from app.models.product import Product, UnitOfMeasure, BusinessStatus
from app.models.manufacturer import Manufacturer
from app.models.inventory_balance import InventoryBalance

MOCK_XML = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
    <NFe>
        <infNFe versao="4.00" Id="NFe311905">
            <ide><nNF>5566</nNF><serie>1</serie><dhEmi>2026-05-13T12:00:00</dhEmi></ide>
            <emit><CNPJ>12345</CNPJ><xNome>MOCK SUPPLIER</xNome></emit>
            <det nItem="1">
                <prod>
                    <xProd>AMOXICILINA 500MG</xProd>
                    <qCom>100.00</qCom>
                    <vUnCom>1.50</vUnCom>
                    <rastro><nLote>B-777</nLote><qLote>100.00</qLote><dVal>2029-01-01</dVal></rastro>
                </prod>
            </det>
        </infNFe>
    </NFe>
</nfeProc>
"""

async def lab_reconciliation():
    print("--- INBOUND RECONCILIATION & LEDGER LABORATORY ---")
    
    async with AsyncSessionLocal() as db:
        # 0. Setup Context & Data
        tenant_res = await db.execute(select(Tenant).limit(1))
        tenant = tenant_res.scalar_one()
        unit = (await db.execute(select(Unit).where(Unit.tenant_id == tenant.id).limit(1))).scalar_one()
        sector = (await db.execute(select(Sector).where(Sector.unit_id == unit.id).limit(1))).scalar_one()

        # Create a real product to match against
        import time
        unique_sku = f"AMX-500-{int(time.time())}"
        p = Product(
            tenant_id=tenant.id,
            sku=unique_sku,
            name="AMOXICILINA 500MG COMPRIMIDO",
            unit_of_measure=UnitOfMeasure.UNIT,
            status=BusinessStatus.ACTIVE
        )
        db.add(p)
        
        m = Manufacturer(corporate_name="LABORATORIO TESTE S.A.")
        db.add(m)
        await db.flush()
        
        # 1. Create Staging Session
        print("\n[1] Creating Staging Session from XML...")
        entry_service = StockEntryService(db)
        session = await entry_service.create_session_from_xml(tenant.id, unit.id, sector.id, MOCK_XML)
        print(f"[SUCCESS] Session {session.id} created (Status: {session.status})")

        # 2. Fuzzy Match Discovery
        print("\n[2] Performing Fuzzy Discovery for items...")
        reconciler = InboundReconciler(db)
        fuzzy = FuzzyReconciler(db)
        
        from app.models.inbound import InboundItem
        items = (await db.execute(select(InboundItem).where(InboundItem.session_id == session.id))).scalars().all()
        
        for item in items:
            print(f"   Searching matches for: '{item.raw_product_name}'")
            suggestions = await fuzzy.search_products(item.raw_product_name, tenant.id)
            for s in suggestions:
                print(f"   - Found: {s['label']} (Score: {s['score']})")
                
            # Simulate operator selection (choosing the top match)
            if suggestions:
                print(f"   Reconciling with: {suggestions[0]['label']}")
                await reconciler.reconcile_item(item.id, product_id=suggestions[0]['id'], manufacturer_id=m.id)

        # 3. Commit to Ledger
        print("\n[3] Committing Session to Ledger...")
        ledger_service = InboundLedgerService(db)
        await ledger_service.commit_session(session.id, created_by="lab_operator")
        print(f"[SUCCESS] Session Committed (Status: {session.status})")

        # 4. Verify Balance
        print("\n[4] Verifying Batch-Scoped Balance...")
        # Get the reconciled item to see which product was matched
        item_res = await db.execute(select(InboundItem).where(InboundItem.session_id == session.id).limit(1))
        matched_item = item_res.scalar_one()
        
        balance_res = await db.execute(
            select(InventoryBalance).where(
                InventoryBalance.product_id == matched_item.product_id,
                InventoryBalance.batch_number == "B-777"
            )
        )
        balance = balance_res.scalar_one()
        print(f"[SUCCESS] Balance for Batch B-777: {balance.balance} units.")
        print(f"   Product matched: {matched_item.product_id}")

        print("\n--- LABORATORY SUCCESSFUL ---")
        print("Causal link proven: XML -> Staging -> Fuzzy Match -> Ledger -> Batch Balance.")

if __name__ == "__main__":
    asyncio.run(lab_reconciliation())
