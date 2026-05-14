import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.services.catalog_orchestrator import CatalogOrchestrator
from app.models.organization import Tenant, Unit, Sector
from app.models.product import Product, IntegrationStatus
import app.db.base  # Ensure all models are registered

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5434/almox_db"

async def run_lab():
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        # 1. Setup Mock Context
        tenant = (await db.execute(select(Tenant))).scalars().first()
        if not tenant:
            print("Creating Mock Tenant...")
            tenant = Tenant(name="Município de Teste", slug="teste-mg")
            db.add(tenant)
            await db.flush()
        
        unit = (await db.execute(select(Unit))).scalars().first()
        if not unit:
            print("Creating Mock Unit...")
            unit = Unit(name="UPA Teste", tenant_id=tenant.id)
            db.add(unit)
            await db.flush()

        orchestrator = CatalogOrchestrator(db)

        # SCENARIO 1: Happy Path
        print("\n--- SCENARIO 1: HAPPY PATH ---")
        data_ok = {
            "name": f"AMOXICILINA 500MG - {uuid.uuid4().hex[:4]}",
            "sku": f"SKU-{uuid.uuid4().hex[:6]}",
            "form_id": "CPS",
            "external_code": "12345"
        }
        res_ok = await orchestrator.register_medicine(tenant.id, unit.id, data_ok)
        print(f"Result: {res_ok['status']} | Intent: {res_ok['intent_id']}")

        # SCENARIO 2: Failure on Link & Retry
        print("\n--- SCENARIO 2: LINK FAILURE & RETRY ---")
        data_fail = {
            "name": f"DIPIRONA 500MG - {uuid.uuid4().hex[:4]}",
            "sku": f"SKU-{uuid.uuid4().hex[:6]}",
            "form_id": "GTS",
            "external_code": "67890",
            "FORCE_FAIL_LINK": True
        }
        res_fail = await orchestrator.register_medicine(tenant.id, unit.id, data_fail)
        print(f"Initial Result: {res_fail['status']} | Step: {res_fail['step']}")
        
        product_id = res_fail.get("product_id")
        if product_id:
            # Check status
            p = await db.get(Product, product_id)
            print(f"Product Integration Status: {p.integration_status}")
            
            print("Executing Retry...")
            # We must clear the FORCE_FAIL_LINK logic or just use retry_link which doesn't have it
            retry_success = await orchestrator.retry_link(tenant.id, unit.id, product_id)
            print(f"Retry Result: {'SUCCESS' if retry_success else 'FAILED'}")
            
            # Check final status
            await db.refresh(p)
            print(f"Final Product Integration Status: {p.integration_status}")

        await db.commit()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_lab())
