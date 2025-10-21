from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import statement_router
from app.database import Base, engine


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(statement_router, prefix=settings.API_V1_PREFIX)

    return app


# Create database tables
Base.metadata.create_all(bind=engine)

# Create application instance
app = create_application()


@app.get("/", tags=["health"])
def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        Status information
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get(f"{settings.API_V1_PREFIX}/", tags=["health"])
def api_health_check() -> dict:
    """
    API health check endpoint.

    Returns:
        API information
    """
    return {
        "message": "Polito-Log API is running",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs"
    }
