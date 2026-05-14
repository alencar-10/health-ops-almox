import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.organization import CodeSequence
from fastapi import HTTPException

class CodeGeneratorService:
    """
    Handles transactional, tenant-scoped numeric code generation.
    Implements ADR-009.
    """
    
    @staticmethod
    async def get_next_code(db: AsyncSession, tenant_id: uuid.UUID, entity_type: str) -> int:
        """
        Generates the next numeric code for a given tenant and entity.
        Uses SELECT FOR UPDATE for row-level locking.
        """
        # 1. Lock the sequence row
        query = select(CodeSequence).where(
            CodeSequence.tenant_id == tenant_id,
            CodeSequence.entity_type == entity_type
        ).with_for_update()
        
        result = await db.execute(query)
        sequence = result.scalar_one_or_none()
        
        if not sequence:
            # If no sequence exists, we create one with default range (1,000,000)
            # This is a fallback; usually sequences should be pre-configured.
            sequence = CodeSequence(
                tenant_id=tenant_id,
                entity_type=entity_type,
                start_range=1000000,
                current_value=1000000
            )
            db.add(sequence)
            await db.flush()
            # Re-lock to be safe
            result = await db.execute(query)
            sequence = result.scalar_one()

        # 2. Increment
        code_to_return = sequence.current_value + 1
        sequence.current_value = code_to_return
        
        # 3. Flush (don't commit here, let the caller decide)
        await db.flush()
        
        return code_to_return

    @staticmethod
    async def configure_sequence(
        db: AsyncSession, 
        tenant_id: uuid.UUID, 
        entity_type: str, 
        start_range: int
    ):
        """
        Configures or updates a sequence range for a tenant.
        """
        query = select(CodeSequence).where(
            CodeSequence.tenant_id == tenant_id,
            CodeSequence.entity_type == entity_type
        ).with_for_update()
        
        result = await db.execute(query)
        sequence = result.scalar_one_or_none()
        
        if sequence:
            # If sequence already started, we only allow increasing the range 
            # if the current value is below the new start range
            if sequence.current_value > start_range:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot reset range to {start_range}. Current value is already {sequence.current_value}."
                )
            sequence.start_range = start_range
            sequence.current_value = start_range
        else:
            sequence = CodeSequence(
                tenant_id=tenant_id,
                entity_type=entity_type,
                start_range=start_range,
                current_value=start_range
            )
            db.add(sequence)
        
        await db.flush()
        return sequence
