import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from app.models.inventory_movement import MovementType
from app.schemas.active_ingredient import StandardResponse

class InventoryMovementBase(BaseModel):
    product_id: uuid.UUID
    type: MovementType
    quantity: float
    reason: str | None = None
    reference_document: str | None = None
    created_by: str

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be greater than zero")
        return v

    @model_validator(mode="after")
    def validate_reason_if_adjustment(self) -> "InventoryMovementBase":
        if self.type == MovementType.ADJUSTMENT and not self.reason:
            raise ValueError("Reason is required for ADJUSTMENT movements")
        return self

class MovementCreate(InventoryMovementBase):
    pass

# NO MovementUpdate or MovementDelete (ADR-004)

class MovementRead(InventoryMovementBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
