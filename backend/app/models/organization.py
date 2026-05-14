import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base
from typing import List

class Tenant(Base):
    """
    Top-level Organization (e.g., a City Hall or a Private Hospital Group).
    """
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    
    # Relationships
    units: Mapped[List["Unit"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    sequences: Mapped[List["CodeSequence"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Unit(Base):
    """
    Operational Unit within a Tenant (e.g., Central Warehouse, Municipal Hospital).
    """
    __tablename__ = "units"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True) # CNES or internal code
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="units")
    sectors: Mapped[List["Sector"]] = relationship(back_populates="unit", cascade="all, delete-orphan")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Sector(Base):
    """
    Specific operational sector within a Unit (e.g., Pharmacy, Emergency, Surgery).
    """
    __tablename__ = "sectors"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Relationships
    unit: Mapped["Unit"] = relationship(back_populates="sectors")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class CodeSequence(Base):
    """
    Manages numeric code generation per tenant and entity type.
    Implements ADR-009.
    """
    __tablename__ = "code_sequences"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., 'product', 'order'
    
    start_range: Mapped[int] = mapped_column(nullable=False, server_default="1000000")
    current_value: Mapped[int] = mapped_column(nullable=False, server_default="1000000")
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="sequences")

    __mapper_args__ = {"eager_defaults": True}
