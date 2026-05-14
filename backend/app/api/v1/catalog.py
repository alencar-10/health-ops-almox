import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.services.catalog_orchestrator import CatalogOrchestrator
from pydantic import BaseModel

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

class MedicineRegisterRequest(BaseModel):
    name: str
    form_id: str
    group_id: str
    subgroup_id: str
    uom_id: str
    sku: str | None = None
    external_code: str | None = None

@router.post("/register-medicine")
async def register_medicine(
    request: MedicineRegisterRequest,
    tenant_id: uuid.UUID,
    unit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    orchestrator = CatalogOrchestrator(db)
    result = await orchestrator.register_medicine(
        tenant_id=tenant_id,
        unit_id=unit_id,
        data=request.model_dump()
    )
    
    # Robust serialization for any dict returned
    safe_result = {k: (str(v) if isinstance(v, uuid.UUID) else v) for k, v in result.items()}
    
    if safe_result["status"] == "FAILED":
        status_code = 409 if safe_result.get("step") == "CHECK_EXISTING" else 500
        raise HTTPException(status_code=status_code, detail=safe_result)
        
    return safe_result

@router.get("/find-similar")
async def find_similar(
    name: str,
    tenant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Search for similar products to prevent duplication before registration (ADR-015).
    """
    from rapidfuzz import process, fuzz
    from app.models.product import Product
    
    # Load all products for this tenant
    result = await db.execute(select(Product).where(Product.tenant_id == tenant_id))
    products = result.scalars().all()
    
    product_names = [p.name for p in products]
    matches = process.extract(name.upper(), product_names, scorer=fuzz.WRatio, limit=5)
    
    similar = []
    for match_name, score, index in matches:
        if score > 70:
            p = products[index]
            similar.append({
                "id": str(p.id),
                "name": p.name,
                "score": round(score, 1),
                "sku": p.sku
            })
            
    return similar
