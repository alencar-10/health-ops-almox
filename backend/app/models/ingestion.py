import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLAlchemyEnum, func, JSON, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class IngestionStatus(str, enum.Enum):
    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    CONFIRMING = "CONFIRMING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"

class ImportSession(Base):
    __tablename__ = "import_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        server_default=text("gen_random_uuid()")
    )
    # Operational Context (ADR-008/011)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=True)
    unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("units.id", ondelete="RESTRICT"), nullable=True)
    target_sector_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sectors.id", ondelete="RESTRICT"), nullable=True)
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[IngestionStatus] = mapped_column(
        SQLAlchemyEnum(IngestionStatus, name="ingestion_status_enum"), 
        server_default=IngestionStatus.PENDING.value,
        nullable=False
    )
    
    # Metadata
    total_rows: Mapped[int] = mapped_column(server_default="0", nullable=False)
    processed_rows: Mapped[int] = mapped_column(server_default="0", nullable=False)
    error_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

class ImportStaging(Base):
    __tablename__ = "import_staging"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        server_default=text("gen_random_uuid()")
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("import_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Raw data from file row
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Validation results
    is_valid: Mapped[bool] = mapped_column(server_default="true", nullable=False)
    validation_errors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Operational flags
    product_exists: Mapped[bool] = mapped_column(server_default="false", nullable=False)
    manufacturer_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    active_ingredient_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    session = relationship("ImportSession")

class ImportError(Base):
    __tablename__ = "import_errors"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        server_default=text("gen_random_uuid()")
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("import_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    row_number: Mapped[int] = mapped_column(nullable=False)
    field: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_code: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )

    session = relationship("ImportSession")
