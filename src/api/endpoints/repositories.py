"""
API endpoints for GitHub repository operations.
"""
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.repository.models import RepositoryCreate, RepositoryResponse
from src.repository.service import RepositoryService

# Create router
router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository_analysis(
    repository: RepositoryCreate,
    service: RepositoryService = Depends(),
) -> Any:
    """
    Create a new repository analysis job.
    
    This endpoint initiates a GitHub repository analysis process,
    which will analyze the repository for structured data files,
    detect their formats, and extract schema information.
    """
    try:
        return await service.create_repository_analysis(repository)
    except Exception as e:
        logger.exception("Failed to create repository analysis: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create repository analysis: {str(e)}",
        )


@router.get("/", response_model=List[RepositoryResponse])
async def list_repositories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: RepositoryService = Depends(),
) -> Any:
    """
    List all repository analyses.
    
    Returns a paginated list of all repository analyses
    that have been submitted to the system.
    """
    try:
        return await service.list_repositories(skip=skip, limit=limit)
    except Exception as e:
        logger.exception("Failed to list repositories: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list repositories: {str(e)}",
        )


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: str,
    service: RepositoryService = Depends(),
) -> Any:
    """
    Get a specific repository analysis by ID.
    
    Returns detailed information about a repository analysis,
    including its status and processing results.
    """
    try:
        repository = await service.get_repository(repository_id)
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository analysis with ID {repository_id} not found",
            )
        return repository
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get repository %s: %s", repository_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get repository: {str(e)}",
        )


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repository_id: str,
    service: RepositoryService = Depends(),
) -> None:
    """
    Delete a repository analysis by ID.
    
    Removes a repository analysis and its associated data from the system.
    """
    try:
        deleted = await service.delete_repository(repository_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository analysis with ID {repository_id} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete repository %s: %s", repository_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete repository: {str(e)}",
        )


@router.post("/{repository_id}/analyze", response_model=Dict[str, Any])
async def trigger_repository_analysis(
    repository_id: str,
    service: RepositoryService = Depends(),
) -> Any:
    """
    Trigger analysis for an existing repository.
    
    This endpoint initiates or re-runs the analysis process for an
    existing repository. This is useful for updating the analysis
    after changes to the repository.
    """
    try:
        result = await service.trigger_analysis(repository_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository with ID {repository_id} not found",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to trigger analysis for repository %s: %s", repository_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger analysis: {str(e)}",
        )
