import uuid
from contextvars import ContextVar
from typing import Optional

# Operational Context State (ADR-008)
# These vars are isolated per request/task
tenant_id: ContextVar[Optional[uuid.UUID]] = ContextVar("tenant_id", default=None)
unit_id: ContextVar[Optional[uuid.UUID]] = ContextVar("unit_id", default=None)
sector_id: ContextVar[Optional[uuid.UUID]] = ContextVar("sector_id", default=None)

def get_current_tenant_id() -> Optional[uuid.UUID]:
    return tenant_id.get()

def get_current_unit_id() -> Optional[uuid.UUID]:
    return unit_id.get()

def set_operational_context(
    t_id: Optional[uuid.UUID] = None, 
    u_id: Optional[uuid.UUID] = None,
    s_id: Optional[uuid.UUID] = None
):
    tenant_id.set(t_id)
    unit_id.set(u_id)
    sector_id.set(s_id)
