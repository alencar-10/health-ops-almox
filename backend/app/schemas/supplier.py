import uuid
import re
from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict, field_validator, EmailStr
from app.models.supplier import SupplierStatus
from app.schemas.active_ingredient import StandardResponse

class SupplierBase(BaseModel):
    corporate_name: str
    trade_name: str | None = None
    document: str | None = None
    contact_name: str | None = None
    email: str | None = None # Using str instead of EmailStr for MVP simplicity/flexibility
    phone: str | None = None
    status: SupplierStatus = SupplierStatus.ACTIVE

    @field_validator("document")
    @classmethod
    def normalize_document(cls, v: str | None) -> str | None:
        if v is None:
            return None
        # ADR-002: Only numbers, trim
        clean_v = re.sub(r"\D", "", v).strip()
        return clean_v if clean_v else None

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    corporate_name: str | None = None
    trade_name: str | None = None
    document: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    status: SupplierStatus | None = None

    @field_validator("document")
    @classmethod
    def normalize_document(cls, v: str | None) -> str | None:
        if v is None:
            return None
        clean_v = re.sub(r"\D", "", v).strip()
        return clean_v if clean_v else None

class SupplierRead(SupplierBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
