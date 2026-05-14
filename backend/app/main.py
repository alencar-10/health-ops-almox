import uuid
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api import health
from app.api.v1 import active_ingredients, manufacturers, suppliers, products, movements, ingestion, organization, inventory, integration, inbound, catalog
from app.core.config import settings
from app.core.logging import correlation_id, logger

from app.core.dependencies import validate_operational_context

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    # 1. Resolve Correlation ID (ADR-007)
    request_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    c_token = correlation_id.set(request_id)
    
    try:
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = request_id
        return response
    finally:
        correlation_id.reset(c_token)

# Base health check
app.include_router(health.router, prefix="/almox/health", tags=["Infrastructure"])

# V1 API
app.include_router(
    active_ingredients.router, 
    prefix="/almox/v1/active-ingredients", 
    tags=["Active Ingredients"]
)
app.include_router(
    manufacturers.router, 
    prefix="/almox/v1/manufacturers", 
    tags=["Manufacturers"]
)
app.include_router(
    suppliers.router, 
    prefix="/almox/v1/suppliers", 
    tags=["Suppliers"]
)
app.include_router(
    products.router, 
    prefix="/almox/v1/products", 
    tags=["Products"]
)
app.include_router(
    movements.router, 
    prefix="/almox/v1/inventory-movements", 
    tags=["Inventory Movements"]
)
app.include_router(
    ingestion.router, 
    prefix="/almox/v1/ingestion", 
    tags=["Ingestion"]
)
app.include_router(
    organization.router, 
    prefix="/almox/v1/organization", 
    tags=["Organization"]
)
app.include_router(
    inventory.router, 
    prefix="/almox/v1/inventory", 
    tags=["Inventory Admin"]
)
app.include_router(
    integration.router, 
    prefix="/almox/v1/integration", 
    tags=["Integration Audit"]
)
app.include_router(
    inbound.router, 
    prefix="/almox/v1/inbound", 
    tags=["Inbound Operations"]
)
app.include_router(
    catalog.router, 
    prefix="/almox/v1/catalog", 
    tags=["Catalog Operations"]
)

@app.get("/")
async def root():
    return {"message": "Vivver Almox MVP API is running"}
