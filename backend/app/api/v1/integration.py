from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.models.integration_log import IntegrationLog
from app.models.product import Product
import uuid

router = APIRouter()

@router.get("/pendencies")
async def get_integration_pendencies(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Query(...),
    limit: int = 20,
    offset: int = 0
):
    """
    Returns products that failed integration or are stuck in the pipeline.
    """
    # Optimized query to include last error category
    query = (
        select(Product)
        .where(Product.tenant_id == tenant_id)
        .where(Product.integration_status.in_(["FAILED", "PENDING", "PRODUCT_SYNCED"]))
        .order_by(desc(Product.created_at))
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    return products

@router.post("/retry/{product_id}")
async def retry_integration(
    product_id: uuid.UUID,
    tenant_id: uuid.UUID = Query(...),
    unit_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers a manual retry for a failed integration.
    """
    from app.services.catalog_orchestrator import CatalogOrchestrator
    orchestrator = CatalogOrchestrator(db)
    success = await orchestrator.retry_link(tenant_id, unit_id, product_id)
    
    return {"success": success}

@router.get("/logs/{intent_id}")
async def get_integration_logs(
    intent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the forensic audit trail for a specific integration intent.
    """
    query = (
        select(IntegrationLog)
        .where(IntegrationLog.intent_id == intent_id)
        .order_by(IntegrationLog.created_at)
    )
    
    result = await db.execute(query)
    return result.scalars().all()
