import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator, Field
from app.models.product import UnitOfMeasure
from app.schemas.active_ingredient import StandardResponse

class ProductBase(BaseModel):
    sku: str
    ean: str | None = None
    name: str
    unit_of_measure: UnitOfMeasure
    minimum_stock: float = 0.0
    active_ingredient_id: uuid.UUID | None = None
    manufacturer_id: uuid.UUID | None = None

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, v: str) -> str:
        # Requirement 4: Mandatory, uppercase, trim
        return v.strip().upper()

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    sku: str | None = None
    ean: str | None = None
    name: str | None = None
    unit_of_measure: UnitOfMeasure | None = None
    minimum_stock: float | None = None
    active_ingredient_id: uuid.UUID | None = None
    manufacturer_id: uuid.UUID | None = None

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip().upper()

class ProductRead(ProductBase):
    id: uuid.UUID
    internal_code: int | None = None
    stock_current: float # Exposed in read, but not in create/update
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
