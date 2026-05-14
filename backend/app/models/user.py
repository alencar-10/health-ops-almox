import uuid
from sqlalchemy import String, ForeignKey, DateTime, func, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Operational Workspace (Sticky Context)
    last_active_unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("units.id"), nullable=True)
    last_active_sector_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sectors.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Permissions
    unit_access = relationship("UserUnitAccess", back_populates="user")
    sector_access = relationship("UserSectorAccess", back_populates="user")

class UserUnitAccess(Base):
    """Link between User and Unit (Allowed Units)"""
    __tablename__ = "user_unit_access"
    __table_args__ = (
        Index("ix_user_unit_lookup", "user_id", "unit_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("units.id", ondelete="CASCADE"), nullable=False)
    
    user = relationship("User", back_populates="unit_access")
    unit = relationship("Unit")

class UserSectorAccess(Base):
    """Link between User and Sector (Allowed Sectors)"""
    __tablename__ = "user_sector_access"
    __table_args__ = (
        Index("ix_user_sector_lookup", "user_id", "sector_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sector_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False)
    
    user = relationship("User", back_populates="sector_access")
    sector = relationship("Sector")

class ContextSwitchLog(Base):
    """Audit log for operational context changes (ADR-013)"""
    __tablename__ = "context_switch_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    from_tenant_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    from_unit_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    from_sector_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    
    to_tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    to_unit_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    to_sector_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    
    # Forensic Metadata (ADR-013)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True) # IPv6 support
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
