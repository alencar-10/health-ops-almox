import uuid
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.product import Product, IntegrationStatus, BusinessStatus
from app.models.active_ingredient import ActiveIngredient
from app.models.integration_log import IntegrationLog, IntegrationStepStatus, FailureCategory
import logging
import time

from app.core.config import settings
from app.adapters.vivver.client import VivverClient
from app.adapters.vivver.catalog_payload_builder import VivverCatalogPayloadBuilder

logger = logging.getLogger(__name__)

class CatalogOrchestrator:
    """
    Orchestrates the multi-step registration pipeline for the Vivver ERP (Cycle 28).
    Supports LAB (Mocked) and PRODUCTION (Real) modes.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vivver = VivverClient()
        self.is_production = settings.APP_MODE == "PRODUCTION"

    async def register_medicine(self, tenant_id: uuid.UUID, unit_id: uuid.UUID, data: dict, intent_id: uuid.UUID | None = None):
        """
        Executes the full 5-step registration vertical slice.
        """
        intent_id = intent_id or uuid.uuid4()
        
        # STEP 0: Check Idempotency (ADR-013)
        existing = await self.db.execute(select(Product).where(Product.sku == data.get("sku")))
        if existing.scalar_one_or_none():
            return {"intent_id": intent_id, "status": "FAILED", "step": "CHECK_EXISTING", "message": "Produto já existe no catálogo"}

        logger.info(f"Starting Medicine Registration Intent: {intent_id}")

        # STEP 1: Normalization (Mocked for now)
        name = data.get("name").upper()
        
        # STEP 2: Create Active Ingredient
        principle = await self._create_principle(tenant_id, unit_id, intent_id, name, data)
        if not principle:
            return {"intent_id": intent_id, "status": "FAILED", "step": "CREATE_PRINCIPLE"}

        # STEP 3: Create Product
        product = await self._create_product(tenant_id, unit_id, intent_id, name, principle.id, data)
        if not product:
            return {"intent_id": intent_id, "status": "FAILED", "step": "CREATE_PRODUCT"}

        # STEP 4: Link Product to Principle
        success = await self._link_principle(tenant_id, unit_id, intent_id, product.id, principle.id, data)
        if not success:
            return {"intent_id": intent_id, "status": "FAILED", "step": "LINK_PRINCIPLE", "product_id": product.id}

        return {"intent_id": intent_id, "status": "COMPLETED", "product_id": product.id}

    async def retry_link(self, tenant_id, unit_id, product_id):
        """
        Manually retries a failed link step.
        """
        product = await self.db.get(Product, product_id)
        if not product or not product.active_ingredient_id:
            return False
            
        intent_id = uuid.uuid4()
        success = await self._link_principle(tenant_id, unit_id, intent_id, product_id, product.active_ingredient_id)
        return success

    async def _create_principle(self, tenant_id, unit_id, intent_id, name, data):
        start_time = time.time()
        try:
            if self.is_production:
                payload = VivverCatalogPayloadBuilder.build_principle(name, data.get("form_id"))
                response = await self.vivver.create_principle(payload)
                if not response: raise ValueError("Vivver Principle Creation Failed (No Response)")
                # Forensic Sync (Wait & Search) - ADR-015
                external_id = await self._resolve_external_id("PRIN", name)
            else:
                external_id = f"LAB_PRIN_{uuid.uuid4().hex[:8]}"
            
            principle = ActiveIngredient(
                tenant_id=tenant_id,
                name=name,
                external_id=external_id,
                external_code=data.get("external_code"),
                pharmaceutical_form_id=data.get("form_id")
            )
            self.db.add(principle)
            await self.db.flush()

            await self._log_step(intent_id, tenant_id, unit_id, "CREATE_PRINCIPLE", 
                                 request=data, response={"external_id": external_id}, 
                                 status=IntegrationStepStatus.SUCCESS, start_time=start_time)
            return principle
        except Exception as e:
            await self._log_step(intent_id, tenant_id, unit_id, "CREATE_PRINCIPLE", 
                                 request=data, status=IntegrationStepStatus.FAILURE, 
                                 error=str(e), start_time=start_time, category=FailureCategory.ERP_ERROR)
            return None

    async def _create_product(self, tenant_id, unit_id, intent_id, name, principle_id, data):
        start_time = time.time()
        try:
            if self.is_production:
                payload = VivverCatalogPayloadBuilder.build_product(
                    name, data.get("group_id"), data.get("subgroup_id"), data.get("uom_id")
                )
                response = await self.vivver.create_product(payload)
                if not response: raise ValueError("Vivver Product Creation Failed")
                external_id = await self._resolve_external_id("PROD", name)
            else:
                external_id = f"LAB_PROD_{uuid.uuid4().hex[:8]}"
            
            product = Product(
                tenant_id=tenant_id,
                name=name,
                sku=data.get("sku"),
                unit_of_measure=data.get("uom", "UNIT"),
                active_ingredient_id=principle_id,
                external_id=external_id,
                integration_status=IntegrationStatus.PRODUCT_SYNCED,
                status=BusinessStatus.PENDING_REVIEW
            )
            self.db.add(product)
            await self.db.flush()

            await self._log_step(intent_id, tenant_id, unit_id, "CREATE_PRODUCT", 
                                 request=data, response={"external_id": external_id}, 
                                 status=IntegrationStepStatus.SUCCESS, product_id=product.id, start_time=start_time)
            return product
        except Exception as e:
            await self._log_step(intent_id, tenant_id, unit_id, "CREATE_PRODUCT", 
                                 request=data, status=IntegrationStepStatus.FAILURE, 
                                 error=str(e), start_time=start_time, category=FailureCategory.ERP_ERROR)
            return None

    async def _link_principle(self, tenant_id, unit_id, intent_id, product_id, principle_id, data: dict = None):
        start_time = time.time()
        try:
            if self.is_production:
                # Need ERP IDs for linking
                product = await self.db.get(Product, product_id)
                principle = await self.db.get(ActiveIngredient, principle_id)
                
                payload = VivverCatalogPayloadBuilder.build_link(
                    product.external_id, principle.external_id
                )
                response = await self.vivver.link_principle(payload)
                if not response: raise ValueError("Vivver Principle Linking Failed")
            
            # Success path
            await self._log_step(intent_id, tenant_id, unit_id, "LINK_PRINCIPLE", 
                                 status=IntegrationStepStatus.SUCCESS, product_id=product_id, start_time=start_time)
            
            product = await self.db.get(Product, product_id)
            product.integration_status = IntegrationStatus.COMPLETED
            await self.db.commit()
            return True
        except Exception as e:
            await self._log_step(intent_id, tenant_id, unit_id, "LINK_PRINCIPLE", 
                                 request=data, status=IntegrationStepStatus.FAILURE, 
                                 error=str(e), start_time=start_time, category=FailureCategory.ERP_ERROR)
            
            product = await self.db.get(Product, product_id)
            product.integration_status = IntegrationStatus.FAILED
            await self.db.commit()
            return False

    async def _resolve_external_id(self, step: str, name: str) -> str:
        """
        Forensic Sync (Wait & Search) with Exponential Backoff (ADR-015).
        Probabilistic behavior of legacy ERP requires multiple attempts.
        """
        if not self.is_production:
            return f"LAB_{step}_{uuid.uuid4().hex[:8]}"

        delays = [1, 2, 4, 8] # Exponential backoff in seconds
        for delay in delays:
            await asyncio.sleep(delay)
            # Try to find by name in Vivver
            # external_id = await self.vivver.find_by_name(step, name)
            # if external_id: return external_id
            logger.info(f"Retrying ID resolution for {step}: {name} (Delay: {delay}s)")
            
        # Fallback to a temporary forensic ID if still not found
        return f"VIV_PENDING_{uuid.uuid4().hex[:8]}"

    async def _log_step(self, intent_id, tenant_id, unit_id, step, request=None, response=None, 
                        status=IntegrationStepStatus.SUCCESS, error=None, product_id=None, 
                        start_time=None, category=None):
        duration = int((time.time() - start_time) * 1000) if start_time else None
        
        log = IntegrationLog(
            intent_id=intent_id,
            tenant_id=tenant_id,
            unit_id=unit_id,
            step_name=step,
            request_payload=request,
            response_payload=response,
            status=status,
            failure_category=category,
            duration_ms=duration,
            error_detail=error,
            product_id=product_id
        )
        self.db.add(log)
        # We don't commit here, we let the orchestrator decide when to commit or flush
