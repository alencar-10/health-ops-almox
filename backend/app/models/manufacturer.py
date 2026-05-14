import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLAlchemyEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base
import enum

class SupplierStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"

class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    
    # Vivver External Reference
    external_id: Mapped[str | None] = mapped_column(String(50)) # codfabricante
    
    corporate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Document normalized (only numbers), unique only if not null
    document: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    
    status: Mapped[SupplierStatus] = mapped_column(
        SQLAlchemyEnum(SupplierStatus), 
        server_default=SupplierStatus.ACTIVE.value,
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
        return f"<Manufacturer(corporate_name={self.corporate_name}, document={self.document})>"
