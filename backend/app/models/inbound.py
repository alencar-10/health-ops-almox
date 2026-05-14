import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLAlchemyEnum, func, ForeignKey, Numeric, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class InboundStatus(str, enum.Enum):
    NEW = "NEW"                 # Raw import
    MATCHED = "MATCHED"         # IA suggested, awaiting human confirmation
    CONFIRMED = "CONFIRMED"     # Human approved the matches
    POSTED = "POSTED"           # Committed to Local Ledger
    ERP_SYNCED = "ERP_SYNCED"   # Successfully pushed to Vivver
    DIVERGENT = "DIVERGENT"     # Local != ERP (Conflict)
    FAILED = "FAILED"           # Permanent error

class InboundType(str, enum.Enum):
    MANUAL = "MANUAL"
    XML_NFE = "XML_NFE"
    TRANSFER = "TRANSFER"

class InboundSession(Base):
    """
    Staging area for stock entries (ADR-012).
    Acts as the 'RecebimentoAggregate' for fiscal and manual operations.
    """
    __tablename__ = "inbound_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("units.id"), nullable=False)
    sector_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sectors.id"), nullable=False)
    
    type: Mapped[InboundType] = mapped_column(SQLAlchemyEnum(InboundType), default=InboundType.MANUAL)
    status: Mapped[InboundStatus] = mapped_column(SQLAlchemyEnum(InboundStatus), default=InboundStatus.NEW)
    
    # Fiscal / Document Metadata
    external_reference: Mapped[str | None] = mapped_column(String(255)) # Invoice/Document Number
    document_type: Mapped[str | None] = mapped_column(String(50)) # codtipodocumento
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("suppliers.id"))
    supplier_name: Mapped[str | None] = mapped_column(String(255))
    
    total_value: Mapped[float | None] = mapped_column(Numeric(15, 2))
    
    # Contract/Request Links (Vivver specific)
    contract_number: Mapped[str | None] = mapped_column(String(100))
    request_number: Mapped[str | None] = mapped_column(String(100))
    
    # Metadata for reconciliation (GTINs, names from XML)
    raw_metadata: Mapped[dict | None] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items: Mapped[list["InboundItem"]] = relationship("InboundItem", back_populates="session", cascade="all, delete-orphan")

class InboundItem(Base):
    """
    Individual items within an inbound session.
    Must be matched against the Catalog before completion.
    """
    __tablename__ = "inbound_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inbound_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Matching
    product_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    manufacturer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("manufacturers.id"), nullable=True)
    
    # External Metadata (for reconciliation)
    raw_product_name: Mapped[str | None] = mapped_column(String(500))
    raw_manufacturer_name: Mapped[str | None] = mapped_column(String(500))
    raw_gtin: Mapped[str | None] = mapped_column(String(64))
    
    # Identity Dimensions (ADR-012)
    batch_number: Mapped[str] = mapped_column(String(64), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Quantities
    quantity_received: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(15, 4), server_default="0.0000")
    
    # Explainable Matching (Cycle 28)
    is_matched: Mapped[bool] = mapped_column(default=False)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    match_metadata: Mapped[dict | None] = mapped_column(JSONB) # Warnings, matched fields
    
    # Audit & Reversal (Cycle 28) - ADR-014
    is_blocked: Mapped[bool] = mapped_column(server_default="false", default=False) # Sanitary violation
    reconciliation_history: Mapped[dict | None] = mapped_column(JSONB, server_default="[]", default=list) # List of previous matches
    confirmation_metadata: Mapped[dict | None] = mapped_column(JSONB) # Who confirmed, when, override reason
    
    error_message: Mapped[str | None] = mapped_column(String(500))

    session: Mapped[InboundSession] = relationship("InboundSession", back_populates="items")
    product = relationship("Product")
