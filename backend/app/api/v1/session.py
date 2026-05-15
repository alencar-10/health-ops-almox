from fastapi import APIRouter, Depends, HTTPException
from app.core.auth.factory import AuthEngineFactory
from app.core.config import settings
from app.schemas.common import StandardResponse

router = APIRouter()

@router.get("/current", response_model=StandardResponse[dict])
async def get_real_session_context():
    """
    Vertical Slice: Fetches the real operational context from the Vivver Auth Engine.
    """
    try:
        engine = AuthEngineFactory.get_engine()
        # In a real app, we'd use the user's stored credentials or a session token.
        # For the Vertical Slice, we use the system credentials from settings.
        context = await engine.login(
            username=settings.VIVVER_USER,
            password=settings.VIVVER_PASS,
            tenant_id=settings.VITE_MUNICIPALITY_ID
        )
        
        if not context:
            raise HTTPException(status_code=401, detail="Failed to resolve real ERP context.")
            
        return {
            "data": {
                "prefecture": {
                    "id": context.tenant_id,
                    "name": context.prefecture_name
                },
                "unit": {
                    "id": context.unit_id,
                    "name": context.unit_name
                },
                "sector": {
                    "id": context.sector_id,
                    "name": context.sector_name
                },
                "user": {
                    "id": context.operator_id,
                    "name": context.operator_name,
                    "role": "Gestor"
                },
                "isValid": True
            },
            "message": "Real ERP context resolved successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-units", response_model=StandardResponse[list])
async def list_available_units():
    """
    Exposes the Discovery Engine to the frontend.
    """
    engine = AuthEngineFactory.get_engine()
    units = await engine.list_available_units()
    return {"data": units, "message": "Units discovered via XHR."}
