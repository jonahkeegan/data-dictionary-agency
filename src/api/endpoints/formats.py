"""
API endpoints for format detection operations.
"""
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from src.format_detection.models import FormatDetectionResult, FormatInfo
from src.format_detection.service import FormatDetectionService

# Create router
router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[FormatInfo])
async def list_formats(
    service: FormatDetectionService = Depends(),
) -> Any:
    """
    List all supported data formats.
    
    Returns a list of all data formats that can be detected and processed
    by the system, along with their metadata.
    """
    try:
        return await service.list_formats()
    except Exception as e:
        logger.exception("Failed to list formats: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list formats: {str(e)}",
        )


@router.get("/{format_id}", response_model=FormatInfo)
async def get_format(
    format_id: str,
    service: FormatDetectionService = Depends(),
) -> Any:
    """
    Get information about a specific format.
    
    Returns detailed information about a specific data format,
    including its capabilities and detection patterns.
    """
    try:
        format_info = await service.get_format(format_id)
        if not format_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Format with ID {format_id} not found",
            )
        return format_info
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get format %s: %s", format_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get format: {str(e)}",
        )


@router.post("/detect", response_model=FormatDetectionResult)
async def detect_format(
    file: UploadFile = File(...),
    confidence_threshold: float = Query(0.7, ge=0, le=1),
    service: FormatDetectionService = Depends(),
) -> Any:
    """
    Detect the format of an uploaded file.
    
    Analyzes an uploaded file to determine its format and extracts
    basic schema information if possible.
    """
    try:
        # Read file content
        content = await file.read()
        
        # Reset file pointer for potential further operations
        await file.seek(0)
        
        # Detect format
        return await service.detect_format(
            filename=file.filename,
            content=content,
            confidence_threshold=confidence_threshold,
        )
    except Exception as e:
        logger.exception("Failed to detect format: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect format: {str(e)}",
        )


@router.post("/parse", response_model=Dict[str, Any])
async def parse_file(
    file: UploadFile = File(...),
    format_id: str = Query(None),
    service: FormatDetectionService = Depends(),
) -> Any:
    """
    Parse a file with a specific format parser.
    
    Parses an uploaded file using a specified format parser,
    extracting detailed schema information.
    """
    try:
        # Read file content
        content = await file.read()
        
        # Reset file pointer for potential further operations
        await file.seek(0)
        
        # Parse file
        return await service.parse_file(
            filename=file.filename,
            content=content,
            format_id=format_id,
        )
    except Exception as e:
        logger.exception("Failed to parse file: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse file: {str(e)}",
        )
