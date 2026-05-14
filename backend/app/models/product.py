import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLAlchemyEnum, func, ForeignKey, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

class UnitOfMeasure(str, enum.Enum):
    UNIT = "UNIT"
    BOX = "BOX"
    BOTTLE = "BOTTLE"
    AMPOULE = "AMPOULE"

class BusinessStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"
    PENDING_REVIEW = "PENDING_REVIEW"

class IntegrationStatus(str, enum.Enum):
    PENDING = "PENDING"
    PRINCIPLE_SYNCED = "PRINCIPLE_SYNCED"
    PRODUCT_SYNCED = "PRODUCT_SYNCED"
    LINKED = "LINKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_sku", "sku"),
        Index("ix_products_ean", "ean"),
        Index("ix_products_internal_code", "internal_code"),
        Index("ix_products_name", "name"),
        Index("ix_products_deleted_at", "deleted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        server_default=func.now()
    )
    
    # Tenant Isolation (ADR-011: Product is a Tenant-level Catalog)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=True)
    
    # External References (ERP Compatibility)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True) # DT_RowId
    external_code: Mapped[str | None] = mapped_column(String(50), nullable=True) # codproduto
    
    # Catalog Groupings (External Refs)
    group_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subgroup_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Generated numeric ID (ADR-009) - Global Uniqueness
    internal_code: Mapped[int | None] = mapped_column(nullable=True, unique=True)
    
    sku: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    ean: Mapped[str | None] = mapped_column(String(13), nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    status: Mapped[BusinessStatus] = mapped_column(
        SQLAlchemyEnum(BusinessStatus, name="business_status_enum"),
        server_default=BusinessStatus.PENDING_REVIEW.value,
        nullable=False
    )
    
    integration_status: Mapped[IntegrationStatus] = mapped_column(
        SQLAlchemyEnum(IntegrationStatus, name="integration_status_enum"),
        server_default=IntegrationStatus.PENDING.value,
        nullable=False
    )
    
    # Unit of Measure (Strict Enum)
    unit_of_measure: Mapped[UnitOfMeasure] = mapped_column(
        SQLAlchemyEnum(UnitOfMeasure, name="unit_of_measure_enum"), 
        nullable=False
    )
    
    # Materialized stock moved to InventoryBalance (ADR-011)
    minimum_stock: Mapped[float] = mapped_column(
        Numeric(15, 4), 
        server_default="0.0000",
        nullable=False
    )
    
    # Relationships (ON DELETE RESTRICT)
    active_ingredient_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("active_ingredients.id", ondelete="RESTRICT"),
        nullable=True
    )
    manufacturer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("manufacturers.id", ondelete="RESTRICT"),
        nullable=True
    )
    
    active_ingredient = relationship("ActiveIngredient")
    manufacturer = relationship("Manufacturer")
    
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
        return f"<Product(sku={self.sku}, name={self.name})>"
