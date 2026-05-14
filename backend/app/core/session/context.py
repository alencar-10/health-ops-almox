from typing import Optional, Dict, Any
from pydantic import BaseModel

class OperationalContext(BaseModel):
    """
    O Contrato Sagrado do contexto operacional do HealthOps.
    """
    tenant_id: str
    prefecture_name: str
    unit_id: str
    unit_name: str
    sector_id: str
    sector_name: str
    operator_id: str
    operator_name: str
    app_mode: str = "LAB"
    
    # Metadata for the integration bridge
    auth_token: Optional[str] = None
    session_id: Optional[str] = None
    csrf_token: Optional[str] = None

class SessionState(BaseModel):
    is_active: bool
    context: Optional[OperationalContext] = None
    expires_at: Optional[str] = None
