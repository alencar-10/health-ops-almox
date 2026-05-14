import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base
import enum

class IntegrationStepStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"

class FailureCategory(str, enum.Enum):
    TIMEOUT = "TIMEOUT"
    VALIDATION = "VALIDATION"
    AUTH = "AUTH"
    ERP_ERROR = "ERP_ERROR"
    UNKNOWN = "UNKNOWN"

class IntegrationLog(Base):
    """
    Forensic audit log for external ERP integrations.
    Tracks every step of the stateful pipeline (Arqueologia Operacional).
    """
    __tablename__ = "integration_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    # Correlation ID (The Intent that triggered this pipeline)
    intent_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    
    # Context (Where was this triggered?)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("units.id"), nullable=True)
    
    # The actual step (e.g., 'CREATE_PRINCIPLE', 'LINK_PRODUCT')
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Data Payload (What we sent and what we got back)
    request_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    status: Mapped[IntegrationStepStatus] = mapped_column(
        SQLAlchemyEnum(IntegrationStepStatus, name="integration_step_status_enum"),
        nullable=False
    )
    
    failure_category: Mapped[FailureCategory | None] = mapped_column(
        SQLAlchemyEnum(FailureCategory, name="failure_category_enum"),
        nullable=True
    )
    
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    retry_count: Mapped[int] = mapped_column(server_default="0", nullable=False)
    provider: Mapped[str | None] = mapped_column(String(50), server_default="VIVVER", nullable=True)
    
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # References to created/affected entities
    product_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<IntegrationLog(intent={self.intent_id}, step={self.step_name}, status={self.status})>"
