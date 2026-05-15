import uuid
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class OperationStatus(str, Enum):
    REQUESTED = "REQUESTED"
    NAVIGATING = "NAVIGATING"
    SWITCHING = "SWITCHING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    AUTH_EXPIRED = "AUTH_EXPIRED"
    HYDRATION_FAILED = "HYDRATION_FAILED"
    INVALID_COMBINATION = "INVALID_COMBINATION"
    STALE_CONTEXT = "STALE_CONTEXT"
    COMMIT_FAILED = "COMMIT_FAILED"
    REVALIDATION_FAILED = "REVALIDATION_FAILED"
    MULTIPLE_CHOICES_REQUIRED = "MULTIPLE_CHOICES_REQUIRED"

class ContextOperation(BaseModel):
    id: uuid.UUID
    status: OperationStatus
    target_unit_id: str
    target_sector_id: str
    progress: int = 0
    message: str = "Iniciando manobra..."
    error: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}

class OperationStore:
    """In-memory store for tracking background context operations."""
    _operations: Dict[uuid.UUID, ContextOperation] = {}

    @classmethod
    def create(cls, unit_id: str, sector_id: Optional[str] = None) -> ContextOperation:
        op_id = uuid.uuid4()
        op = ContextOperation(
            id=op_id,
            status=OperationStatus.REQUESTED,
            target_unit_id=unit_id,
            target_sector_id=sector_id or "AUTO_RESOLVE",
            started_at=datetime.now()
        )
        cls._operations[op_id] = op
        return op

    @classmethod
    def get(cls, op_id: uuid.UUID) -> Optional[ContextOperation]:
        return cls._operations.get(op_id)

    @classmethod
    def update(cls, op_id: uuid.UUID, **kwargs):
        if op_id in cls._operations:
            op = cls._operations[op_id]
            for key, value in kwargs.items():
                setattr(op, key, value)
            if op.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.TIMEOUT]:
                op.finished_at = datetime.now()
            cls._operations[op_id] = op
