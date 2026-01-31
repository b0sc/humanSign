from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.api import verify
from app.core.config import settings

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Document authentication via keystroke dynamics",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(verify.router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "HumanSign Decoder API",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.services.ml import model_manager
    
    return {
        "status": "healthy",
        "version": settings.api_version,
        "model_loaded": model_manager.is_model_loaded()
    }

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.api_title,
        version=settings.api_version,
        description="Document authentication via keystroke dynamics",
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi