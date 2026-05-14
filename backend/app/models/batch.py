import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class BatchLot(Base):
    """
    Aggregate for a specific production batch (Cycle 28).
    Owns the identity and metadata of a batch across movements and units.
    """
    __tablename__ = "batch_lots"
    __table_args__ = (
        Index("ix_batch_lots_product_batch", "product_id", "batch_number", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    manufacturer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("manufacturers.id"))
    
    batch_number: Mapped[str] = mapped_column(String(64), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    manufacturing_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product = relationship("Product")
    manufacturer = relationship("Manufacturer")

    def __repr__(self) -> str:
        return f"<BatchLot(product_id={self.product_id}, batch={self.batch_number}, expiry={self.expiry_date.date()})>"
