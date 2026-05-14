import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.common import StandardResponse
from app.services.inventory_rebuild import InventoryRebuildService
from app.services.organization import OrganizationService
from app.core.context import get_current_tenant_id, get_current_unit_id, sector_id as context_sector_id

router = APIRouter()

@router.post("/rebuild-balance", response_model=StandardResponse[dict], tags=["Admin/Maintenance"])
async def rebuild_inventory_balance(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Recalculates the materialized balance for a product in the current active sector.
    This is a maintenance operation to ensure ledger-balance consistency.
    """
    tenant_id = get_current_tenant_id()
    unit_id = get_current_unit_id()
    sector_id = context_sector_id.get()

    if not tenant_id or not sector_id:
        raise HTTPException(status_code=400, detail="Operational context (Tenant, Sector) is required for rebuild.")

    # Validate Hierarchy before rebuild
    await OrganizationService.validate_hierarchy(db, tenant_id=tenant_id, unit_id=unit_id, sector_id=sector_id)
    
    new_balance = await InventoryRebuildService.rebuild_balance(db, product_id, sector_id)
    await db.commit()
    
    return {
        "data": {"product_id": product_id, "sector_id": sector_id, "new_balance": new_balance},
        "message": "Inventory balance rebuilt successfully from ledger."
    }
