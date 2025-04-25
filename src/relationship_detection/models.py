"""
Models for relationship detection operations.
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field


class RelationshipType(str, Enum):
    """Types of relationships between schemas."""
    ONE_TO_ONE = "one_to_one"          # One record relates to exactly one other record
    ONE_TO_MANY = "one_to_many"        # One record relates to multiple records (parent->children)
    MANY_TO_ONE = "many_to_one"        # Multiple records relate to one record (children->parent) 
    MANY_TO_MANY = "many_to_many"      # Multiple records relate to multiple records (requires join)
    INHERITANCE = "inheritance"        # One schema inherits or extends another
    COMPOSITION = "composition"        # One schema contains or embeds another
    REFERENCE = "reference"            # One schema references another without strong relationship


class RelationshipConfidence(BaseModel):
    """Model for relationship confidence information."""
    score: float = Field(..., description="Confidence score between 0.0 and 1.0")
    factors: Dict[str, float] = Field(default_factory=dict, 
                                     description="Factors contributing to confidence score")
    rationale: str = Field("", description="Explanation for the confidence assessment")
    detection_method: str = Field("", description="Method used for relationship detection")


class SchemaRelationship(BaseModel):
    """Model for a relationship between schemas."""
    source_schema: str = Field(..., description="Source schema identifier")
    target_schema: str = Field(..., description="Target schema identifier")
    source_fields: List[str] = Field(..., description="Source fields involved in the relationship")
    target_fields: List[str] = Field(..., description="Target fields involved in the relationship")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    confidence: RelationshipConfidence = Field(..., description="Confidence in the relationship")
    bidirectional: bool = Field(False, description="Whether relationship is navigable in both directions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SchemaRelationshipStore(BaseModel):
    """Storage model for schema relationships."""
    relationships: List[SchemaRelationship] = Field(..., description="List of detected relationships")
    schema_coverage: Dict[str, List[str]] = Field(default_factory=dict, 
                                                description="Maps schemas to related schemas")
    confidence_summary: Dict[str, float] = Field(default_factory=dict, 
                                                description="Summary statistics for confidence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
