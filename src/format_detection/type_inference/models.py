"""
Models for enhanced type inference operations.
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field

from src.format_detection.models import DataType, FieldConstraint


class TypePattern(str, Enum):
    """Patterns that can be detected in types."""
    UUID = "uuid"                     # UUID pattern (e.g. 123e4567-e89b-12d3-a456-426614174000)
    EMAIL = "email"                   # Email pattern
    DATE = "date"                     # Date pattern (e.g. 2025-04-23)
    DATETIME = "datetime"             # DateTime pattern (e.g. 2025-04-23T10:20:30Z)
    URL = "url"                       # URL pattern
    IP_ADDRESS = "ip_address"         # IP address pattern
    PHONE_NUMBER = "phone_number"     # Phone number pattern
    CURRENCY = "currency"             # Currency pattern
    PERCENTAGE = "percentage"         # Percentage pattern
    DURATION = "duration"             # Duration/time period pattern
    GEOLOCATION = "geolocation"       # Geolocation pattern
    BINARY = "binary"                 # Binary data pattern
    ENUM = "enum"                     # Enumeration pattern
    ID = "id"                         # Identifier pattern


class TypeConfidence(BaseModel):
    """Model for type confidence information."""
    score: float = Field(..., description="Confidence score between 0.0 and 1.0")
    factors: Dict[str, float] = Field(default_factory=dict, 
                                     description="Factors contributing to confidence score")
    rationale: str = Field("", description="Explanation for the confidence assessment")
    detection_method: str = Field("", description="Method used for type detection")


class TypeConstraintEnhanced(FieldConstraint):
    """Enhanced model for type constraints with additional metadata."""
    confidence: float = Field(1.0, description="Confidence in the constraint (0.0 to 1.0)")
    source: str = Field("", description="Source of the constraint detection")


class TypeAlternative(BaseModel):
    """Model for alternative type possibilities."""
    type: DataType = Field(..., description="Alternative data type")
    format_specific_type: Optional[str] = Field(None, description="Format-specific type name")
    confidence: float = Field(..., description="Confidence score for this alternative")
    rationale: str = Field("", description="Explanation for suggesting this alternative")


class EnhancedTypeInfo(BaseModel):
    """Model for enhanced type information."""
    primary_type: DataType = Field(..., description="Primary detected data type")
    secondary_types: List[DataType] = Field(default_factory=list, 
                                           description="Secondary compatible types")
    format_specific_type: Optional[str] = Field(None, 
                                               description="Format-specific type name")
    constraints: List[TypeConstraintEnhanced] = Field(default_factory=list, 
                                                    description="Type constraints")
    patterns: List[TypePattern] = Field(default_factory=list, 
                                       description="Detected type patterns")
    confidence: TypeConfidence = Field(..., description="Type confidence information")
    possible_alternatives: List[TypeAlternative] = Field(default_factory=list, 
                                                       description="Alternative type possibilities")
    
    # For complex types
    item_type: Optional["EnhancedTypeInfo"] = Field(None, 
                                                  description="Type of array items")
    key_type: Optional["EnhancedTypeInfo"] = Field(None, 
                                                 description="Type of map/dict keys")
    value_type: Optional["EnhancedTypeInfo"] = Field(None, 
                                                   description="Type of map/dict values")
    properties: Dict[str, "EnhancedTypeInfo"] = Field(default_factory=dict, 
                                                    description="Types of object properties")
    is_nullable: bool = Field(False, description="Whether the type allows null values")
    is_recursive: bool = Field(False, description="Whether the type is recursive")
    is_heterogeneous: bool = Field(False, 
                                  description="Whether collections contain mixed types")
    type_parameters: List["EnhancedTypeInfo"] = Field(default_factory=list, 
                                                    description="Generic type parameters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional type metadata")


# Add self-reference for recursive types
EnhancedTypeInfo.update_forward_refs()


class NormalizedType(BaseModel):
    """Model for normalized type representation across formats."""
    base_type: DataType = Field(..., description="Base normalized data type")
    format: str = Field(..., description="Original format identifier")
    format_specific_type: Optional[str] = Field(None, 
                                              description="Original format-specific type")
    constraints: List[TypeConstraintEnhanced] = Field(default_factory=list, 
                                                    description="Type constraints")
    parameters: List["NormalizedType"] = Field(default_factory=list, 
                                             description="Type parameters")
    properties: Dict[str, "NormalizedType"] = Field(default_factory=dict, 
                                                  description="Object properties")
    is_nullable: bool = Field(False, description="Whether the type allows null values")
    metadata: Dict[str, Any] = Field(default_factory=dict, 
                                    description="Format-specific metadata")


# Add self-reference for recursive types
NormalizedType.update_forward_refs()
