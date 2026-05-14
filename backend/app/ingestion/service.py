import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_, func
from app.models.ingestion import ImportSession, ImportStaging, IngestionStatus, ImportError
from datetime import datetime, timezone
from app.models.product import Product, UnitOfMeasure
from app.models.manufacturer import Manufacturer
from app.models.active_ingredient import ActiveIngredient
from app.models.inventory_movement import MovementType
from app.services.product import ProductService
from app.services.inventory_movement import InventoryMovementService
from app.schemas.product import ProductCreate
from app.schemas.inventory_movement import MovementCreate
from app.core.logging import logger
from fastapi import HTTPException
from typing import List, Dict, Any

class IngestionService:
    @staticmethod
    async def create_session(
        db: AsyncSession, 
        filename: str, 
        created_by: str,
        raw_data_list: List[Dict[str, Any]]
    ):
        """
        Step 1: Save file rows to Staging (ADR-006).
        """
        from app.core.context import get_current_tenant_id, get_current_unit_id, sector_id as context_sector_id
        
        tenant_id = get_current_tenant_id()
        unit_id = get_current_unit_id()
        sector_id = context_sector_id.get()

        session = ImportSession(
            filename=filename,
            created_by=created_by,
            total_rows=len(raw_data_list),
            status=IngestionStatus.PENDING,
            tenant_id=tenant_id,
            unit_id=unit_id,
            target_sector_id=sector_id
        )
        db.add(session)
        await db.flush() # Get session ID

        staging_rows = []
        for row in raw_data_list:
            staging_row = ImportStaging(
                session_id=session.id,
                raw_data=row
            )
            staging_rows.append(staging_row)
        
        db.add_all(staging_rows)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def validate_session(db: AsyncSession, session_id: uuid.UUID):
        """
        Step 2: Dry-run Validation (ADR-006).
        """
        session_query = select(ImportSession).where(ImportSession.id == session_id)
        session = (await db.execute(session_query)).scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Update status to VALIDATING
        session.status = IngestionStatus.VALIDATING
        await db.flush()

        # Clear previous errors for this session
        await db.execute(update(ImportStaging).where(ImportStaging.session_id == session_id).values(validation_errors=None))
        await db.execute(delete(ImportError).where(ImportError.session_id == session_id))

        staging_query = select(ImportStaging).where(ImportStaging.session_id == session_id)
        staging_rows = (await db.execute(staging_query)).scalars().all()

        row_idx = 1
        for row in staging_rows:
            data = row.raw_data
            errors = {}
            
            # 1. Check SKU
            sku_val = data.get("sku")
            sku = str(sku_val).strip().upper() if sku_val is not None else ""
            if not sku or sku == "NONE":
                errors["sku"] = "SKU is mandatory"
                db.add(ImportError(
                    session_id=session_id,
                    row_number=row_idx,
                    field="sku",
                    error_code="MANDATORY_FIELD_MISSING",
                    message="SKU is mandatory"
                ))
            else:
                # Check production - Scoped by Tenant (ADR-011)
                from app.core.context import get_current_tenant_id
                tenant_id = get_current_tenant_id()
                
                prod_query = select(Product).where(Product.sku == sku)
                if tenant_id:
                    prod_query = prod_query.where(Product.tenant_id == tenant_id)
                
                prod = (await db.execute(prod_query)).scalar_one_or_none()
                if prod:
                    row.product_exists = True
            
            # 2. Check Manufacturer
            m_name = data.get("manufacturer")
            if m_name:
                m_query = select(Manufacturer).where(
                    or_(
                        Manufacturer.corporate_name.ilike(m_name),
                        Manufacturer.trade_name.ilike(m_name)
                    )
                )
                m = (await db.execute(m_query)).scalar_one_or_none()
                if m:
                    row.manufacturer_id = m.id
                else:
                    errors["manufacturer"] = f"Manufacturer '{m_name}' not found"
                    db.add(ImportError(
                        session_id=session_id,
                        row_number=row_idx,
                        field="manufacturer",
                        error_code="RELATIONAL_NOT_FOUND",
                        message=f"Manufacturer '{m_name}' not found"
                    ))

            # 3. Check Active Ingredient
            i_name = data.get("active_ingredient")
            if i_name:
                i_query = select(ActiveIngredient).where(ActiveIngredient.name.ilike(i_name))
                i = (await db.execute(i_query)).scalar_one_or_none()
                if i:
                    row.active_ingredient_id = i.id
                else:
                    errors["active_ingredient"] = f"Active Ingredient '{i_name}' not found"
                    db.add(ImportError(
                        session_id=session_id,
                        row_number=row_idx,
                        field="active_ingredient",
                        error_code="RELATIONAL_NOT_FOUND",
                        message=f"Active Ingredient '{i_name}' not found"
                    ))

            # Update row status
            row.validation_errors = errors
            row.is_valid = len(errors) == 0
            row_idx += 1
        
        session.status = IngestionStatus.VALIDATED
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def confirm_import(db: AsyncSession, session_id: uuid.UUID, created_by: str):
        """
        Step 3: Transactional Persistence (ADR-006).
        Includes Idempotence protection.
        """
        session_query = select(ImportSession).where(ImportSession.id == session_id)
        session = (await db.execute(session_query)).scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Idempotence: Block if already confirmed
        if session.status == IngestionStatus.COMPLETED or session.confirmed_at:
            logger.info(f"Ingestion confirm skipped: Session {session_id} already confirmed.")
            return session

        if session.status != IngestionStatus.VALIDATED:
            logger.warning(f"Ingestion confirm failed: Session {session_id} not in VALIDATED state.")
            raise HTTPException(status_code=400, detail="Session not ready for confirmation")

        import time
        start_time = time.time()
        
        logger.info(f"Starting ingestion confirmation for session {session_id}...")

        # Set status to CONFIRMING
        session.status = IngestionStatus.CONFIRMING
        await db.flush()

        staging_query = select(ImportStaging).where(
            ImportStaging.session_id == session_id,
            ImportStaging.is_valid == True
        )
        valid_rows = (await db.execute(staging_query)).scalars().all()

        logger.info(f"Processing {len(valid_rows)} valid rows for session {session_id}")

        processed = 0
        for row in valid_rows:
            data = row.raw_data
            
            if not row.product_exists:
                # Create Product
                p_schema = ProductCreate(
                    sku=data.get("sku"),
                    ean=data.get("ean"),
                    name=data.get("name", "Unnamed Product"),
                    unit_of_measure=data.get("unit_of_measure", "UNIT"),
                    minimum_stock=data.get("minimum_stock", 0.0),
                    active_ingredient_id=row.active_ingredient_id,
                    manufacturer_id=row.manufacturer_id
                )
                product = await ProductService.create(db, p_schema)
                
                # Initial Stock Entry (ADR-011: Contextual Stock)
                initial_stock = data.get("initial_stock", 0.0)
                if initial_stock > 0:
                    # Ingestion confirmer must set the session context to the current task
                    from app.core.context import set_operational_context
                    set_operational_context(
                        t_id=session.tenant_id, 
                        u_id=session.unit_id, 
                        s_id=session.target_sector_id
                    )
                    
                    await InventoryMovementService.create_movement(
                        db,
                        product_id=product.id,
                        type=MovementType.INITIAL_ENTRY,
                        quantity=float(initial_stock),
                        created_by=created_by,
                        reference_document=f"Import Session {session.id}"
                    )
                
                processed += 1
        
        session.processed_rows = processed
        session.status = IngestionStatus.COMPLETED
        session.confirmed_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(session)
        
        duration = time.time() - start_time
        rows_per_sec = processed / duration if duration > 0 else 0
        
        logger.info(
            f"Ingestion confirmation complete for session {session_id}.",
            extra={"extra_fields": {
                "duration": round(duration, 3),
                "processed_rows": processed,
                "rows_per_sec": round(rows_per_sec, 2)
            }}
        )
        return session
