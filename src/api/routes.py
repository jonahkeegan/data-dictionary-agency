"""
API routes for the Data Dictionary Agency application.
"""
from fastapi import APIRouter

from src.api.endpoints import formats, repositories, schemas

# Create main API router
router = APIRouter()

# Include sub-routers for different endpoints
router.include_router(
    repositories.router,
    prefix="/repositories",
    tags=["Repositories"],
)

router.include_router(
    formats.router,
    prefix="/formats",
    tags=["Formats"],
)

router.include_router(
    schemas.router,
    prefix="/schemas",
    tags=["Schemas"],
)
