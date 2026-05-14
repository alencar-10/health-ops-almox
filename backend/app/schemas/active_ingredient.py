from datetime import datetime
import uuid
from typing import Generic, TypeVar, List
from pydantic import BaseModel, ConfigDict
from app.models.active_ingredient import ProductStatus

from app.schemas.common import StandardResponse

# Active Ingredient Schemas
class ActiveIngredientBase(BaseModel):
    name: str
    description: str | None = None
    status: ProductStatus = ProductStatus.ACTIVE

class ActiveIngredientCreate(ActiveIngredientBase):
    pass

class ActiveIngredientUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: ProductStatus | None = None

class ActiveIngredientRead(ActiveIngredientBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
