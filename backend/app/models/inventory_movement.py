import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLAlchemyEnum, func, ForeignKey, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class MovementType(str, enum.Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    ADJUSTMENT = "ADJUSTMENT"
    INITIAL_ENTRY = "INITIAL_ENTRY"
    REVERSAL = "REVERSAL"

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        Index("ix_inventory_movements_product_id", "product_id"),
        Index("ix_inventory_movements_type", "type"),
        Index("ix_inventory_movements_sector_id", "sector_id"),
        Index("ix_inventory_movements_created_at", "created_at"),
        Index("ix_inventory_movements_batch", "batch_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        server_default=func.now()
    )
    # Tenant, Unit & Sector Isolation (ADR-008/011)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=True)
    unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("units.id", ondelete="RESTRICT"), nullable=True)
    sector_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sectors.id", ondelete="RESTRICT"), nullable=True)
    
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Identity Dimensions (ADR-012)
    batch_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    type: Mapped[MovementType] = mapped_column(
        SQLAlchemyEnum(MovementType, name="movement_type_enum"), 
        nullable=False
    )
    quantity: Mapped[float] = mapped_column(
        Numeric(15, 4), 
        nullable=False
    )
    
    # Required for ADJUSTMENT (Requirement 9)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Operational Reference (Requirement 11)
    reference_document: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Audit (Requirement 10)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )

    product = relationship("Product")

    def __repr__(self) -> str:
        return f"<InventoryMovement(type={self.type}, quantity={self.quantity}, product_id={self.product_id})>"
