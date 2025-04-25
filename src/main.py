"""
Data Dictionary Agency - Main Application Module
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router as api_router
from src.core.config import settings
from src.core.logging import configure_logging

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    application.include_router(api_router, prefix=settings.API_PREFIX)

    @application.get("/", tags=["Health"])
    async def health_check():
        """Health check endpoint for the application."""
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "environment": settings.APP_ENV,
        }

    @application.on_event("startup")
    async def startup_event():
        logger.info(
            "Starting Data Dictionary Agency - %s environment",
            settings.APP_ENV,
        )

    @application.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down Data Dictionary Agency")

    return application


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
