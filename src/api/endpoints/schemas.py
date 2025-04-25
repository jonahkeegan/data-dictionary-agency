"""
API endpoints for schema operations.
"""
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.db.models import SchemaCreate, SchemaResponse, SchemaUpdate
from src.db.service import SchemaService

# Create router
router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[SchemaResponse])
async def list_schemas(
    repository_id: str = Query(None),
    format_id: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: SchemaService = Depends(),
) -> Any:
    """
    List all extracted schemas.
    
    Returns a paginated list of all schemas that have been extracted
    from data files, with optional filtering by repository or format.
    """
    try:
        return await service.list_schemas(
            repository_id=repository_id,
            format_id=format_id,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.exception("Failed to list schemas: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list schemas: {str(e)}",
        )


@router.get("/{schema_id}", response_model=SchemaResponse)
async def get_schema(
    schema_id: str,
    service: SchemaService = Depends(),
) -> Any:
    """
    Get a specific schema by ID.
    
    Returns detailed information about a specific schema,
    including its fields, relationships, and metadata.
    """
    try:
        schema = await service.get_schema(schema_id)
        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema with ID {schema_id} not found",
            )
        return schema
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get schema %s: %s", schema_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schema: {str(e)}",
        )


@router.post("/", response_model=SchemaResponse, status_code=status.HTTP_201_CREATED)
async def create_schema(
    schema: SchemaCreate,
    service: SchemaService = Depends(),
) -> Any:
    """
    Create a new schema manually.
    
    Allows manual creation of schema information,
    which can be useful for testing or creating reference schemas.
    """
    try:
        return await service.create_schema(schema)
    except Exception as e:
        logger.exception("Failed to create schema: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schema: {str(e)}",
        )


@router.put("/{schema_id}", response_model=SchemaResponse)
async def update_schema(
    schema_id: str,
    schema_update: SchemaUpdate,
    service: SchemaService = Depends(),
) -> Any:
    """
    Update a schema by ID.
    
    Updates information about a specific schema, such as
    its fields, relationships, or metadata.
    """
    try:
        schema = await service.update_schema(schema_id, schema_update)
        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema with ID {schema_id} not found",
            )
        return schema
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to update schema %s: %s", schema_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update schema: {str(e)}",
        )


@router.delete("/{schema_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schema(
    schema_id: str,
    service: SchemaService = Depends(),
) -> None:
    """
    Delete a schema by ID.
    
    Removes a schema and its associated data from the system.
    """
    try:
        deleted = await service.delete_schema(schema_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema with ID {schema_id} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete schema %s: %s", schema_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete schema: {str(e)}",
        )


@router.get("/{schema_id}/relationships", response_model=List[Dict[str, Any]])
async def get_schema_relationships(
    schema_id: str,
    service: SchemaService = Depends(),
) -> Any:
    """
    Get relationships for a specific schema.
    
    Returns all detected relationships that involve the specified schema,
    including relationships to other schemas.
    """
    try:
        relationships = await service.get_schema_relationships(schema_id)
        if relationships is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema with ID {schema_id} not found",
            )
        return relationships
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get relationships for schema %s: %s", schema_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schema relationships: {str(e)}",
        )


@router.post("/{schema_id}/export", response_model=Dict[str, Any])
async def export_schema(
    schema_id: str,
    format: str = Query("json", description="Export format (json, yaml, sql, etc.)"),
    service: SchemaService = Depends(),
) -> Any:
    """
    Export a schema to a specific format.
    
    Generates an export of the schema in the specified format,
    such as JSON, YAML, SQL DDL, etc.
    """
    try:
        export_data = await service.export_schema(schema_id, format)
        if export_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema with ID {schema_id} not found",
            )
        return export_data
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Failed to export schema %s: %s", schema_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export schema: {str(e)}",
        )
