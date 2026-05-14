import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.organization import Tenant, Unit, Sector

class OrganizationService:
    @staticmethod
    async def create_tenant(db: AsyncSession, name: str, slug: str):
        tenant = Tenant(name=name, slug=slug)
        db.add(tenant)
        await db.flush()
        return tenant

    @staticmethod
    async def create_unit(db: AsyncSession, tenant_id: uuid.UUID, name: str, code: str | None = None):
        unit = Unit(tenant_id=tenant_id, name=name, code=code)
        db.add(unit)
        await db.flush()
        
        # Automate Default Sector (Cycle 12)
        default_sector = Sector(unit_id=unit.id, name="GERAL")
        db.add(default_sector)
        await db.flush()
        
        return unit

    @staticmethod
    async def create_sector(db: AsyncSession, unit_id: uuid.UUID, name: str):
        sector = Sector(unit_id=unit_id, name=name)
        db.add(sector)
        await db.flush()
        return sector

    @staticmethod
    async def get_tenant_by_id(db: AsyncSession, tenant_id: uuid.UUID):
        query = select(Tenant).where(Tenant.id == tenant_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_unit_by_id(db: AsyncSession, unit_id: uuid.UUID):
        query = select(Unit).where(Unit.id == unit_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_sector_by_id(db: AsyncSession, sector_id: uuid.UUID):
        query = select(Sector).where(Sector.id == sector_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def validate_hierarchy(
        db: AsyncSession, 
        tenant_id: uuid.UUID, 
        unit_id: uuid.UUID | None = None, 
        sector_id: uuid.UUID | None = None
    ):
        """
        Enforces strict hierarchical isolation (ADR-011).
        Ensures that provided Unit belongs to Tenant and Sector belongs to Unit.
        """
        if unit_id:
            unit = await OrganizationService.get_unit_by_id(db, unit_id)
            if not unit or unit.tenant_id != tenant_id:
                raise HTTPException(status_code=403, detail="Hierarchy Violation: Unit does not belong to Tenant.")
            
            if sector_id:
                sector = await OrganizationService.get_sector_by_id(db, sector_id)
                if not sector or sector.unit_id != unit_id:
                    raise HTTPException(status_code=403, detail="Hierarchy Violation: Sector does not belong to Unit.")

    @staticmethod
    async def get_tenant_by_slug(db: AsyncSession, slug: str):
        query = select(Tenant).where(Tenant.slug == slug)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_tenants(db: AsyncSession):
        query = select(Tenant).order_by(Tenant.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def list_units(db: AsyncSession, tenant_id: uuid.UUID):
        query = select(Unit).where(Unit.tenant_id == tenant_id).order_by(Unit.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def list_sectors(db: AsyncSession, unit_id: uuid.UUID):
        query = select(Sector).where(Sector.unit_id == unit_id).order_by(Sector.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_available_contexts(db: AsyncSession, user_id: uuid.UUID, tenant_id: uuid.UUID):
        """
        Returns a hierarchical map of Units and Sectors authorized for the given User.
        Implements Permission-First Context Discovery (Cycle 21).
        """
        from app.models.user import UserUnitAccess, UserSectorAccess
        
        # 1. Get authorized Units
        unit_query = (
            select(Unit)
            .join(UserUnitAccess, UserUnitAccess.unit_id == Unit.id)
            .where(UserUnitAccess.user_id == user_id)
            .where(Unit.tenant_id == tenant_id)
            .order_by(Unit.name)
        )
        units_result = await db.execute(unit_query)
        authorized_units = units_result.scalars().all()
        
        # 2. Get authorized Sectors
        sector_query = (
            select(Sector)
            .join(UserSectorAccess, UserSectorAccess.sector_id == Sector.id)
            .join(Unit, Sector.unit_id == Unit.id)
            .where(UserSectorAccess.user_id == user_id)
            .where(Unit.tenant_id == tenant_id)
            .order_by(Sector.name)
        )
        sectors_result = await db.execute(sector_query)
        authorized_sectors = sectors_result.scalars().all()
        
        # 3. Build hierarchy
        hierarchy = []
        for unit in authorized_units:
            unit_sectors = [s for s in authorized_sectors if s.unit_id == unit.id]
            hierarchy.append({
                "id": unit.id,
                "name": unit.name,
                "code": unit.code,
                "sectors": [{"id": s.id, "name": s.name} for s in unit_sectors]
            })
            
        return hierarchy
