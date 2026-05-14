import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.ingestion import IngestionStatus
from typing import List, Dict, Any

class SessionRead(BaseModel):
    id: uuid.UUID
    filename: str
    status: IngestionStatus
    total_rows: int
    processed_rows: int
    error_summary: Dict[str, Any] | None = None
    created_by: str
    confirmed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StagingRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    raw_data: Dict[str, Any]
    is_valid: bool
    validation_errors: Dict[str, Any] | None = None
    product_exists: bool

    model_config = ConfigDict(from_attributes=True)

class ImportErrorRead(BaseModel):
    id: uuid.UUID
    row_number: int
    field: str | None = None
    error_code: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IngestionPreview(BaseModel):
    session: SessionRead
    rows: List[StagingRead]
    errors: List[ImportErrorRead] = []
