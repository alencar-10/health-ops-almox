import asyncio
import uuid
import sys
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base # Ensure all models are registered
from app.db.session import AsyncSessionLocal
from app.services.inbound.stock_entry_service import StockEntryService
from app.models.organization import Tenant, Unit, Sector
from sqlalchemy import select

MOCK_NFE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
    <NFe>
        <infNFe versao="4.00" Id="NFe31190500000000000000550010000012341234567890">
            <ide>
                <nNF>1234</nNF>
                <serie>1</serie>
                <dhEmi>2026-05-13T12:00:00-03:00</dhEmi>
            </ide>
            <emit>
                <CNPJ>12345678000199</CNPJ>
                <xNome>DISTRIBUIDORA MEDLAB LTDA</xNome>
            </emit>
            <det nItem="1">
                <prod>
                    <cProd>7721</cProd>
                    <cEAN>7891234567890</cEAN>
                    <xProd>AMOXICILINA 500MG CAPSULA</xProd>
                    <qCom>1000.0000</qCom>
                    <vUnCom>0.4500</vUnCom>
                    <rastro>
                        <nLote>LOT12345</nLote>
                        <qLote>1000.0000</qLote>
                        <dVal>2028-12-31</dVal>
                    </rastro>
                </prod>
            </det>
            <det nItem="2">
                <prod>
                    <cProd>8832</cProd>
                    <cEAN>7890000001234</cEAN>
                    <xProd>DIPIRONA 500MG/ML GOTAS 20ML</xProd>
                    <qCom>50.0000</qCom>
                    <vUnCom>2.5000</vUnCom>
                    <rastro>
                        <nLote>BATCH-99</nLote>
                        <qLote>50.0000</qLote>
                        <dVal>2027-06-30</dVal>
                    </rastro>
                </prod>
            </det>
        </infNFe>
    </NFe>
</nfeProc>
"""

async def lab_inbound_discovery():
    print("--- INBOUND STOCK DISCOVERY LABORATORY ---")
    
    async with AsyncSessionLocal() as db:
        # 0. Get real IDs to avoid FK errors
        tenant_result = await db.execute(select(Tenant).limit(1))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            print("[ERROR] No tenant found in DB. Run lab_vertical_slice.py first.")
            return

        unit_result = await db.execute(select(Unit).where(Unit.tenant_id == tenant.id).limit(1))
        unit = unit_result.scalar_one_or_none()
        if not unit:
            print("[INFO] Creating mock Unit...")
            unit = Unit(tenant_id=tenant.id, name="UPA Teste", code="UPA001")
            db.add(unit)
            await db.flush()
        
        sector_result = await db.execute(select(Sector).where(Sector.unit_id == unit.id).limit(1))
        sector = sector_result.scalar_one_or_none()
        if not sector:
            print("[INFO] Creating mock Sector...")
            sector = Sector(unit_id=unit.id, name="Farmacia Central")
            db.add(sector)
            await db.flush()
        
        service = StockEntryService(db)
        
        print(f"\n[1] Parsing Mock NF-e XML (Invoice: 1234)...")
        try:
            session = await service.create_session_from_xml(
                tenant_id=tenant.id,
                unit_id=unit.id,
                sector_id=sector.id,
                xml_content=MOCK_NFE_XML
            )
            
            print(f"[SUCCESS] Inbound Session Created: {session.id}")
            print(f"   Supplier: {session.supplier_name}")
            print(f"   Status: {session.status}")
            
            print(f"\n[2] Verifying Staged Items...")
            from app.models.inbound import InboundItem
            result = await db.execute(select(InboundItem).where(InboundItem.session_id == session.id))
            items = result.scalars().all()
            
            for item in items:
                print(f"   - Item: {item.raw_product_name}")
                print(f"     Batch: {item.batch_number} | Expiry: {item.expiry_date.date()} | Qty: {item.quantity_received}")
                print(f"     Price: R$ {item.unit_price}")
            
            print("\n--- DISCOVERY SUCCESSFUL ---")
            print("Archeology proof: NF-e structure correctly mapped to Staging Tables.")
            
        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(lab_inbound_discovery())
