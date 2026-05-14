import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.ingestion.parsers import IngestionParser
from app.ingestion.service import IngestionService
from app.models.ingestion import ImportSession, ImportStaging, ImportError
from app.schemas.ingestion import SessionRead, IngestionPreview
from app.schemas.common import StandardResponse
from typing import List

router = APIRouter()

@router.post("/upload", response_model=StandardResponse[SessionRead])
async def upload_file(
    file: UploadFile = File(...),
    created_by: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 1: Upload and Stage.
    """
    content = await file.read()
    try:
        raw_data = IngestionParser.parse_file(file, content)
        # Required columns for Product import
        IngestionParser.validate_columns(raw_data, ["sku", "name", "unit_of_measure"])
        
        session = await IngestionService.create_session(
            db, file.filename, created_by, raw_data
        )
        return {"data": session, "message": "File uploaded and staged successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/validate/{session_id}", response_model=StandardResponse[SessionRead])
async def validate_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2: Dry-run Validation.
    """
    session = await IngestionService.validate_session(db, session_id)
    return {"data": session, "message": "Validation complete"}

@router.get("/preview/{session_id}", response_model=StandardResponse[IngestionPreview])
async def get_preview(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 3: Show results.
    """
    session_query = select(ImportSession).where(ImportSession.id == session_id)
    session = (await db.execute(session_query)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    staging_query = select(ImportStaging).where(ImportStaging.session_id == session_id)
    rows = (await db.execute(staging_query)).scalars().all()
    
    errors_query = select(ImportError).where(ImportError.session_id == session_id)
    errors = (await db.execute(errors_query)).scalars().all()
    
    return {
        "data": {
            "session": session, 
            "rows": rows,
            "errors": errors
        },
        "message": "success"
    }

@router.post("/confirm/{session_id}", response_model=StandardResponse[SessionRead])
async def confirm_import(
    session_id: uuid.UUID,
    created_by: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 4: Finalize.
    """
    session = await IngestionService.confirm_import(db, session_id, created_by)
    return {"data": session, "message": "Import completed successfully"}
