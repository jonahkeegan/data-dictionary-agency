"""
Database models for the Data Dictionary Agency application.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from src.format_detection.models import DataType, FieldInfo, SchemaDetails


class SchemaType(str, Enum):
    """Enum for schema types."""
    TABLE = "table"
    DOCUMENT = "document"
    STRUCT = "struct"
    OBJECT = "object"
    RECORD = "record"
    MESSAGE = "message"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class RelationshipType(str, Enum):
    """Enum for relationship types."""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"
    PARENT_CHILD = "parent_child"
    REFERENCE = "reference"
    UNKNOWN = "unknown"


class SchemaCreate(BaseModel):
    """Model for creating a schema."""
    repository_id: str = Field(..., description="Repository ID")
    file_path: str = Field(..., description="Path to the file within repository")
    name: str = Field(..., description="Schema name")
    format_id: str = Field(..., description="Format ID")
    schema_type: SchemaType = Field(..., description="Schema type")
    description: Optional[str] = Field(None, description="Schema description")
    details: SchemaDetails = Field(..., description="Schema details")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SchemaDB(BaseModel):
    """Database model for a schema."""
    id: str = Field(..., description="Unique identifier")
    repository_id: str = Field(..., description="Repository ID")
    file_path: str = Field(..., description="Path to the file within repository")
    name: str = Field(..., description="Schema name")
    format_id: str = Field(..., description="Format ID")
    schema_type: SchemaType = Field(..., description="Schema type")
    description: Optional[str] = Field(None, description="Schema description")
    details: SchemaDetails = Field(..., description="Schema details")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class SchemaResponse(SchemaDB):
    """Response model for a schema."""
    pass


class SchemaUpdate(BaseModel):
    """Model for updating a schema."""
    name: Optional[str] = Field(None, description="Schema name")
    schema_type: Optional[SchemaType] = Field(None, description="Schema type")
    description: Optional[str] = Field(None, description="Schema description")
    details: Optional[SchemaDetails] = Field(None, description="Schema details")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RelationshipCreate(BaseModel):
    """Model for creating a relationship."""
    source_schema_id: str = Field(..., description="Source schema ID")
    target_schema_id: str = Field(..., description="Target schema ID")
    relationship_type: RelationshipType = Field(..., description="Relationship type")
    source_fields: List[str] = Field(..., description="Source schema fields")
    target_fields: List[str] = Field(..., description="Target schema fields")
    confidence: float = Field(..., description="Confidence score (0 to 1)")
    description: Optional[str] = Field(None, description="Relationship description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RelationshipDB(BaseModel):
    """Database model for a relationship."""
    id: str = Field(..., description="Unique identifier")
    source_schema_id: str = Field(..., description="Source schema ID")
    target_schema_id: str = Field(..., description="Target schema ID")
    relationship_type: RelationshipType = Field(..., description="Relationship type")
    source_fields: List[str] = Field(..., description="Source schema fields")
    target_fields: List[str] = Field(..., description="Target schema fields")
    confidence: float = Field(..., description="Confidence score (0 to 1)")
    description: Optional[str] = Field(None, description="Relationship description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class RelationshipResponse(RelationshipDB):
    """Response model for a relationship."""
    pass


class RelationshipUpdate(BaseModel):
    """Model for updating a relationship."""
    relationship_type: Optional[RelationshipType] = Field(None, description="Relationship type")
    source_fields: Optional[List[str]] = Field(None, description="Source schema fields")
    target_fields: Optional[List[str]] = Field(None, description="Target schema fields")
    confidence: Optional[float] = Field(None, description="Confidence score (0 to 1)")
    description: Optional[str] = Field(None, description="Relationship description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
