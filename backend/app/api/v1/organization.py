import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.organization import Unit, Sector
from fastapi import APIRouter, Depends, HTTPException, Request
from app.schemas.organization import (
    TenantRead, TenantCreate,
    UnitRead, UnitCreate,
    SectorRead, SectorCreate
)
from app.schemas.common import StandardResponse
from app.services.organization import OrganizationService
from app.core.context import get_current_tenant_id, get_current_unit_id, set_operational_context
from app.models.user import ContextSwitchLog
from typing import List, Any

router = APIRouter()

@router.get("/me", response_model=StandardResponse[dict])
async def get_current_context_info(db: AsyncSession = Depends(get_db)):
    """
    Returns the currently resolved operational context details.
    """
    t_id = get_current_tenant_id()
    u_id = get_current_unit_id()
    # Also get sector from contextvar if available
    from app.core.context import sector_id as context_sector_id
    s_id = context_sector_id.get()
    
    tenant = await OrganizationService.get_tenant_by_id(db, t_id) if t_id else None
    unit = await OrganizationService.get_unit_by_id(db, u_id) if u_id else None
    sector = await OrganizationService.get_sector_by_id(db, s_id) if s_id else None
    
    return {
        "data": {
            "tenant": tenant,
            "unit": unit,
            "sector": sector
        },
        "message": "success"
    }

@router.get("/available", response_model=StandardResponse[List[dict]])
async def get_available_contexts(db: AsyncSession = Depends(get_db)):
    """
    Returns the hierarchical list of Units and Sectors the user can access.
    Implements Permission-First Context Discovery (Cycle 21).
    """
    tenant_id = get_current_tenant_id()
    # MOCK USER: using a fixed UUID until auth is implemented
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001") 
    
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required.")
        
    hierarchy = await OrganizationService.get_available_contexts(db, user_id, tenant_id)
    return {"data": hierarchy, "message": "success"}

@router.post("/switch", response_model=StandardResponse[dict])
async def switch_operational_context(
    request: Request,
    target_tenant_id: uuid.UUID,
    target_unit_id: uuid.UUID,
    target_sector_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Validates, audits, and persists a context switch (Sticky Context).
    """
    from app.core.logging import correlation_id
    from app.models.user import User
    
    # 1. Validate Hierarchy (ADR-011)
    await OrganizationService.validate_hierarchy(
        db, 
        tenant_id=target_tenant_id, 
        unit_id=target_unit_id, 
        sector_id=target_sector_id
    )
    
    # 2. Audit & Persist Sticky Context (ADR-013)
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001") 
    
    # Update User Workspace (Sticky Context)
    user = await db.get(User, user_id)
    if user:
        user.last_active_unit_id = target_unit_id
        user.last_active_sector_id = target_sector_id
    
    # Capture metadata
    ip_addr = request.client.host if request.client else None
    ua = request.headers.get("User-Agent")
    curr_corr_id = correlation_id.get()
    
    audit = ContextSwitchLog(
        user_id=user_id,
        from_tenant_id=get_current_tenant_id(),
        from_unit_id=get_current_unit_id(),
        to_tenant_id=target_tenant_id,
        to_unit_id=target_unit_id,
        to_sector_id=target_sector_id,
        ip_address=ip_addr,
        user_agent=ua,
        correlation_id=curr_corr_id
    )
    db.add(audit)
    await db.commit()
    
    return {
        "data": {
            "active_context": {
                "tenant_id": target_tenant_id,
                "unit_id": target_unit_id,
                "sector_id": target_sector_id
            }
        },
        "message": "Context switched successfully and persisted for next session."
    }

@router.get("/tenants", response_model=StandardResponse[List[TenantRead]])
async def list_tenants(db: AsyncSession = Depends(get_db)):
    tenants = await OrganizationService.list_tenants(db)
    return {"data": tenants, "message": "success"}

@router.post("/tenants", response_model=StandardResponse[TenantRead], status_code=201)
async def create_tenant(payload: TenantCreate, db: AsyncSession = Depends(get_db)):
    tenant = await OrganizationService.create_tenant(db, **payload.model_dump())
    await db.commit()
    await db.refresh(tenant)
    return {"data": tenant, "message": "created successfully"}

@router.get("/tenants/{tenant_id}/units", response_model=StandardResponse[List[UnitRead]])
async def list_units(tenant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    units = await OrganizationService.list_units(db, tenant_id)
    return {"data": units, "message": "success"}

@router.post("/units", response_model=StandardResponse[UnitRead], status_code=201)
async def create_unit(payload: UnitCreate, db: AsyncSession = Depends(get_db)):
    unit = await OrganizationService.create_unit(db, **payload.model_dump())
    await db.commit()
    await db.refresh(unit)
    return {"data": unit, "message": "created successfully"}

@router.get("/units/{unit_id}/sectors", response_model=StandardResponse[List[SectorRead]])
async def list_sectors(unit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    sectors = await OrganizationService.list_sectors(db, unit_id)
    return {"data": sectors, "message": "success"}

@router.post("/sectors", response_model=StandardResponse[SectorRead], status_code=201)
async def create_sector(payload: SectorCreate, db: AsyncSession = Depends(get_db)):
    sector = await OrganizationService.create_sector(db, **payload.model_dump())
    await db.commit()
    await db.refresh(sector)
    return {"data": sector, "message": "created successfully"}
