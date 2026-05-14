import uuid
from sqlalchemy import ForeignKey, Numeric, Index, func, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base_class import Base

class InventoryBalance(Base):
    """
    Materialized stock level for a product at a specific operational location.
    Scoped by Tenant -> Unit -> Sector (ADR-011).
    """
    __tablename__ = "inventory_balances"
    __table_args__ = (
        # Guarantee unique balance per product/location/batch
        Index("ix_inv_balance_lookup", "product_id", "unit_id", "sector_id", "batch_number", unique=True),
        Index("ix_inv_balance_tenant", "tenant_id"),
        Index("ix_inv_balance_expiry", "expiry_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    
    # Hierarchy
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("units.id", ondelete="RESTRICT"), nullable=False)
    sector_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sectors.id", ondelete="RESTRICT"), nullable=False)
    
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    
    # Identity Dimensions (ADR-012)
    batch_number: Mapped[str] = mapped_column(String(64), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Materialized Value
    balance: Mapped[float] = mapped_column(Numeric(15, 4), server_default="0.0000", nullable=False)
    erp_synced_balance: Mapped[float] = mapped_column(Numeric(15, 4), server_default="0.0000", nullable=False) # ADR-014 Drift tracking
    last_synced_movement_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("inventory_movements.id"), nullable=True) # ADR-015 Watermark
    
    # Audit
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Relationships
    product = relationship("Product")
    unit = relationship("Unit")
    sector = relationship("Sector")

    def __repr__(self) -> str:
        return f"<InventoryBalance(product_id={self.product_id}, balance={self.balance}, sector_id={self.sector_id})>"
