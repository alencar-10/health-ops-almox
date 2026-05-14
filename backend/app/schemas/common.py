from typing import TypeVar, Generic, List
from pydantic import BaseModel, Field

T = TypeVar("T")

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str | None = Field(None, description="Field to sort by")
    order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    total_pages: int
    message: str = "success"
    correlation_id: str | None = None

class StandardResponse(BaseModel, Generic[T]):
    data: T
    message: str = "success"
    correlation_id: str | None = None
