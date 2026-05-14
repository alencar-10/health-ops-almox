import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Enum as SQLAlchemyEnum, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base
import enum

class ProductStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"

class ActiveIngredient(Base):
    __tablename__ = "active_ingredients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())

    # Tenant Isolation (ADR-011: Principles are part of the Catalog)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=True)
    
    # External References (ERP Compatibility)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True) # DT_RowId
    external_code: Mapped[str | None] = mapped_column(String(50), nullable=True) # codprincipio
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Pharmaceutical Form (Mandatory for Vivver)
    pharmaceutical_form_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    status: Mapped[ProductStatus] = mapped_column(
        SQLAlchemyEnum(ProductStatus), 
        server_default=ProductStatus.ACTIVE.value,
        nullable=False
    )
    
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
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<ActiveIngredient(name={self.name}, status={self.status})>"
