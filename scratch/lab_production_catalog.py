import asyncio
import uuid
import sys
import os
from unittest.mock import patch, MagicMock

# Mocking app structure
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.db.session import AsyncSessionLocal
from app.services.catalog_orchestrator import CatalogOrchestrator
from app.core.config import settings
from app.models.product import Product
from app.models.active_ingredient import ActiveIngredient
from app.models.manufacturer import Manufacturer
from app.models.supplier import Supplier
from app.models.organization import Tenant, Unit, Sector
from app.models.integration_log import IntegrationLog

async def run_production_catalog_lab():
    print("\n--- [LAB] PRODUCTION CATALOG ORCHESTRATION (CYCLE 28) ---")
    
    # 1. Force PRODUCTION Mode
    settings.APP_MODE = "PRODUCTION"
    print(f"Current Mode: {settings.APP_MODE}")

    async with AsyncSessionLocal() as db:
        # SETUP: IDs
        tenant_id = uuid.UUID("fb0282be-1b58-40ce-a124-1cf897e1a393")
        unit_id = uuid.UUID("3d14d3ea-52f4-42f7-bfa3-4e1fa1aabd42")
        
        data = {
            "name": "PRODUCTION TEST DRUG",
            "form_id": "1",
            "group_id": "01",
            "subgroup_id": "001",
            "uom_id": "1",
            "sku": f"PROD-{uuid.uuid4().hex[:4]}",
            "external_code": "EXT-PROD-01"
        }

        # 2. Mock VivverClient to simulate real ERP response
        orchestrator = CatalogOrchestrator(db)
        
        with patch.object(orchestrator.vivver, 'create_principle', return_value="<html>SUCCESS PRIN</html>") as mock_prin, \
             patch.object(orchestrator.vivver, 'create_product', return_value="<html>SUCCESS PROD</html>") as mock_prod, \
             patch.object(orchestrator.vivver, 'link_principle', return_value="<html>SUCCESS LINK</html>") as mock_link:
            
            print("Executing Vertical Registration (5 steps)...")
            result = await orchestrator.register_medicine(tenant_id, unit_id, data)
            
            # 3. VERIFICATION
            print(f"Result: {result}")
            
            if result["status"] == "COMPLETED":
                print("SUCCESS: Full registration vertical slice completed in PRODUCTION mode.")
                
                # Check DB persistence
                product = await db.get(Product, result["product_id"])
                print(f"Product in DB: {product.name} (External ID: {product.external_id})")
                
                # Check if mocks were called
                print(f"Vivver PRIN Call: {mock_prin.called}")
                print(f"Vivver PROD Call: {mock_prod.called}")
                print(f"Vivver LINK Call: {mock_link.called}")
            else:
                print(f"FAILURE: Registration failed at step {result.get('step')}")

if __name__ == "__main__":
    asyncio.run(run_production_catalog_lab())
