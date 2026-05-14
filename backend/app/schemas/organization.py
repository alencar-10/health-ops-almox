import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

# Tenant
class TenantBase(BaseModel):
    name: str
    slug: str

class TenantCreate(TenantBase):
    pass

class TenantRead(TenantBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Unit
class UnitBase(BaseModel):
    name: str
    code: str | None = None

class UnitCreate(UnitBase):
    tenant_id: uuid.UUID

class UnitRead(UnitBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Sector
class SectorBase(BaseModel):
    name: str

class SectorCreate(SectorBase):
    unit_id: uuid.UUID

class SectorRead(SectorBase):
    id: uuid.UUID
    unit_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
