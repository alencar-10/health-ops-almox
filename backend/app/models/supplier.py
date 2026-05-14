import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLAlchemyEnum, func, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base
import enum

class SupplierStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"

class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    
    # Vivver External Reference
    external_id: Mapped[str | None] = mapped_column(String(50)) # codfornecedor
    
    corporate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True) # codcnpj
    
    # Fiscal / Contract Metadata (Requirement 4)
    contract_number: Mapped[str | None] = mapped_column(String(100))
    contract_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    contract_value: Mapped[float | None] = mapped_column(Numeric(15, 2))
    
    # Contact info
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    status: Mapped[SupplierStatus] = mapped_column(
        SQLAlchemyEnum(SupplierStatus, name="supplier_status_enum"), 
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
        return f"<Supplier(corporate_name={self.corporate_name}, document={self.document})>"
