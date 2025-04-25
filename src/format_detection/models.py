"""
Models for format detection operations.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class FormatType(str, Enum):
    """Enum for format types."""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    YAML = "yaml"
    SQL = "sql"
    AVRO = "avro"
    PARQUET = "parquet"
    PROTOBUF = "protobuf"
    GRAPHQL = "graphql"
    HDF5 = "hdf5"
    ORC = "orc"
    EXCEL = "excel"


class DataType(str, Enum):
    """Enum for data types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    DATE = "date"
    DATETIME = "datetime"
    NULL = "null"
    BINARY = "binary"
    ENUM = "enum"
    UUID = "uuid"
    UNKNOWN = "unknown"


class FieldConstraint(BaseModel):
    """Model for field constraints."""
    type: str = Field(..., description="Type of constraint")
    value: Any = Field(..., description="Value of constraint")
    description: Optional[str] = Field(None, description="Description of constraint")


class FormatInfo(BaseModel):
    """Model for format information."""
    id: str = Field(..., description="Format identifier")
    name: str = Field(..., description="Format display name")
    description: str = Field(..., description="Format description")
    mime_types: List[str] = Field(..., description="Associated MIME types")
    extensions: List[str] = Field(..., description="Associated file extensions")
    capabilities: Dict[str, bool] = Field(..., description="Format capabilities")
    examples: List[str] = Field(..., description="Example patterns")
    schema_type: str = Field(..., description="Type of schema representation")
    version: Optional[str] = Field(None, description="Format version")


class FormatDetectionResult(BaseModel):
    """Model for format detection result."""
    format_id: Optional[str] = Field(None, description="Detected format ID")
    confidence: float = Field(..., description="Detection confidence (0 to 1)")
    mime_type: Optional[str] = Field(None, description="Detected MIME type")
    file_size: int = Field(..., description="File size in bytes")
    detected_encoding: Optional[str] = Field(None, description="Detected character encoding")
    sample_data: Optional[str] = Field(None, description="Sample data preview")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    schema_preview: Optional[Dict[str, Any]] = Field(None, description="Basic schema preview")
    detection_time: float = Field(..., description="Time taken for detection (seconds)")


class FieldInfo(BaseModel):
    """Model for field information."""
    name: str = Field(..., description="Field name")
    path: str = Field(..., description="Path to field (in dot notation)")
    data_type: DataType = Field(..., description="Field data type")
    nullable: bool = Field(False, description="Whether field can be null")
    description: Optional[str] = Field(None, description="Field description")
    constraints: List[FieldConstraint] = Field(default_factory=list, description="Field constraints")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    sample_values: Optional[List[Any]] = Field(None, description="Sample values")
    statistics: Optional[Dict[str, Any]] = Field(None, description="Field statistics")


class SchemaDetails(BaseModel):
    """Model for schema details."""
    fields: List[FieldInfo] = Field(..., description="Schema fields")
    primary_keys: List[str] = Field(default_factory=list, description="Primary key fields")
    foreign_keys: List[Dict[str, Any]] = Field(default_factory=list, description="Foreign key references")
    unique_constraints: List[List[str]] = Field(default_factory=list, description="Unique constraints")
    indices: List[Dict[str, Any]] = Field(default_factory=list, description="Indices")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    dependencies: List[str] = Field(default_factory=list, description="Schema dependencies")


class DetectionOptions(BaseModel):
    """Model for detection options."""
    confidence_threshold: float = Field(0.7, description="Confidence threshold for detection")
    max_sample_size: int = Field(10240, description="Maximum sample size in bytes")
    detect_encoding: bool = Field(True, description="Whether to detect text encoding")
    extract_sample: bool = Field(True, description="Whether to extract data samples")
    extract_schema: bool = Field(True, description="Whether to extract basic schema")
    format_hints: Optional[List[str]] = Field(None, description="Format hints to prioritize")
