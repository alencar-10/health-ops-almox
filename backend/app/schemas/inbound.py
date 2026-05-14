from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.inbound import InboundStatus, InboundType

class InboundItemSchema(BaseModel):
    id: UUID
    session_id: UUID
    product_id: Optional[UUID] = None
    manufacturer_id: Optional[UUID] = None
    raw_product_name: Optional[str] = None
    raw_manufacturer_name: Optional[str] = None
    raw_gtin: Optional[str] = None
    batch_number: str
    expiry_date: datetime
    quantity_received: float
    unit_price: float
    is_matched: bool
    is_blocked: bool = False
    match_score: Optional[float] = None
    match_metadata: Optional[dict] = None
    reconciliation_history: List[dict] = []
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class InboundSessionSchema(BaseModel):
    id: UUID
    tenant_id: UUID
    unit_id: UUID
    sector_id: UUID
    type: InboundType
    status: InboundStatus
    external_reference: Optional[str] = None
    supplier_name: Optional[str] = None
    total_value: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    items: List[InboundItemSchema] = []

    class Config:
        from_attributes = True

class InboundReconcileRequest(BaseModel):
    product_id: UUID
    manufacturer_id: UUID
    score: Optional[float] = None
    metadata: Optional[dict] = None
