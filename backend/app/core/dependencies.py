import uuid
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.organization import Unit
from app.core.context import set_operational_context

async def validate_operational_context(
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
    x_unit_id: str | None = Header(None, alias="X-Unit-ID"),
    x_sector_id: str | None = Header(None, alias="X-Sector-ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Dependency that validates the operational context hierarchy and sets the global context state.
    Implements ADR-010 and ADR-011 (Mandatory Sector).
    """
    if not x_tenant_id:
        return None

    try:
        t_id = uuid.UUID(x_tenant_id)
        u_id = uuid.UUID(x_unit_id) if x_unit_id else None
        s_id = uuid.UUID(x_sector_id) if x_sector_id else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format in context headers")

    if u_id:
        # Validate hierarchy: Unit must belong to Tenant
        query = select(Unit).where(Unit.id == u_id, Unit.tenant_id == t_id)
        result = await db.execute(query)
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Security Violation: Unit does not belong to Tenant.")

    if s_id:
        # Validate hierarchy: Sector must belong to Unit
        if not u_id:
            raise HTTPException(status_code=400, detail="Unit ID is required when providing a Sector ID.")
            
        from app.models.organization import Sector
        query = select(Sector).where(Sector.id == s_id, Sector.unit_id == u_id)
        result = await db.execute(query)
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Security Violation: Sector does not belong to Unit.")

    # Set contextvars for this request
    set_operational_context(t_id=t_id, u_id=u_id, s_id=s_id)
    return {"tenant_id": t_id, "unit_id": u_id, "sector_id": s_id}
