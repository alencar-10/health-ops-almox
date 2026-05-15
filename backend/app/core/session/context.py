from typing import Optional, Dict, Any
from pydantic import BaseModel

class SessionContext(BaseModel):
    """
    Technical session artifacts (Infrastructure/Transport layer).
    """
    session_id: str
    csrf_token: str
    auth_token: Optional[str] = None
    expires_at: Optional[str] = None
    cookies: Optional[Dict[str, str]] = None

class OperationalContext(BaseModel):
    """
    The Sacred Contract of HealthOps Operational Authority (Domain layer).
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
    
    # Linked session (Optional for offline/simulation modes)
    session: Optional[SessionContext] = None

class SessionState(BaseModel):
    is_active: bool
    context: Optional[OperationalContext] = None
