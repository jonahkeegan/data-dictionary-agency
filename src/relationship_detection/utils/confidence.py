"""
Utility functions for calculating confidence and validating relationships.
"""
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from src.format_detection.models import SchemaDetails
from src.relationship_detection.models import (
    RelationshipConfidence,
    RelationshipType,
    SchemaRelationship,
)
from src.relationship_detection.utils.comparators import fields_are_unique


logger = logging.getLogger(__name__)


def calculate_confidence(
    factors: Dict[str, float],
    detection_method: str,
    rationale: str
) -> RelationshipConfidence:
    """
    Calculate confidence from a set of factors.
    
    Args:
        factors: Dictionary of confidence factors and their scores.
        detection_method: Method used for detection.
        rationale: Rationale for the confidence assessment.
        
    Returns:
        RelationshipConfidence: Confidence information.
    """
    # Sum all factors to get base score
    base_score = sum(factors.values())
    
    # Ensure score is within bounds
    confidence_score = max(0.1, min(1.0, base_score))
    
    return RelationshipConfidence(
        score=confidence_score,
        factors=factors,
        rationale=rationale,
        detection_method=detection_method,
    )


def validate_relationship_type(
    source_schema: SchemaDetails,
    target_schema: SchemaDetails,
    source_fields: List[str],
    target_fields: List[str]
) -> RelationshipType:
    """
    Validate and determine the most likely relationship type.
    
    Args:
        source_schema: Source schema.
        target_schema: Target schema.
        source_fields: Source field names.
        target_fields: Target field names.
        
    Returns:
        RelationshipType: Determined relationship type.
    """
    # Check if source and target fields are unique
    source_is_unique = fields_are_unique(source_schema, source_fields)
    target_is_unique = fields_are_unique(target_schema, target_fields)
    
    # Determine relationship type based on uniqueness
    if source_is_unique and target_is_unique:
        return RelationshipType.ONE_TO_ONE
    elif source_is_unique and not target_is_unique:
        return RelationshipType.ONE_TO_MANY
    elif not source_is_unique and target_is_unique:
        return RelationshipType.MANY_TO_ONE
    else:
        return RelationshipType.MANY_TO_MANY


def determine_relationship_direction(
    schema1: SchemaDetails,
    schema2: SchemaDetails,
    schema1_fields: List[str],
    schema2_fields: List[str]
) -> Dict[str, Any]:
    """
    Determine the most likely direction for a relationship.
    
    Args:
        schema1: First schema.
        schema2: Second schema.
        schema1_fields: Fields from first schema.
        schema2_fields: Fields from second schema.
        
    Returns:
        Dict[str, Any]: Relationship direction information.
    """
    # Check if fields in either schema are primary keys or unique
    schema1_fields_unique = fields_are_unique(schema1, schema1_fields)
    schema2_fields_unique = fields_are_unique(schema2, schema2_fields)
    
    # Relationship type logic
    if schema1_fields_unique and schema2_fields_unique:
        # One-to-one: Either direction could work
        rel_type = RelationshipType.ONE_TO_ONE
        bidirectional = True
        direction_confidence = 0.5  # Equal confidence for either direction
        
        # Default direction (arbitrary choice)
        source_schema = schema1
        target_schema = schema2
        source_fields = schema1_fields
        target_fields = schema2_fields
    
    elif schema1_fields_unique and not schema2_fields_unique:
        # One-to-many: schema1 (one) to schema2 (many)
        rel_type = RelationshipType.ONE_TO_MANY
        bidirectional = False
        direction_confidence = 0.7  # Higher confidence for this direction
        
        source_schema = schema1
        target_schema = schema2
        source_fields = schema1_fields
        target_fields = schema2_fields
    
    elif not schema1_fields_unique and schema2_fields_unique:
        # Many-to-one: schema1 (many) to schema2 (one)
        rel_type = RelationshipType.MANY_TO_ONE
        bidirectional = False
        direction_confidence = 0.7  # Higher confidence for this direction
        
        source_schema = schema1
        target_schema = schema2
        source_fields = schema1_fields
        target_fields = schema2_fields
    
    else:
        # Many-to-many: Could be either direction
        rel_type = RelationshipType.MANY_TO_MANY
        bidirectional = True
        direction_confidence = 0.5  # Equal confidence for either direction
        
        # Default direction (arbitrary choice)
        source_schema = schema1
        target_schema = schema2
        source_fields = schema1_fields
        target_fields = schema2_fields
    
    return {
        "source_schema": source_schema,
        "target_schema": target_schema,
        "source_fields": source_fields,
        "target_fields": target_fields,
        "relationship_type": rel_type,
        "bidirectional": bidirectional,
        "direction_confidence": direction_confidence,
    }


def consolidate_relationships(
    relationships: List[SchemaRelationship],
    confidence_threshold: float = 0.5
) -> List[SchemaRelationship]:
    """
    Consolidate and filter relationships.
    
    Args:
        relationships: List of detected relationships.
        confidence_threshold: Minimum confidence threshold.
        
    Returns:
        List[SchemaRelationship]: Consolidated relationships.
    """
    if not relationships:
        return []
    
    # Filter by confidence
    filtered = [r for r in relationships if r.confidence.score >= confidence_threshold]
    
    # Group by source and target schema
    grouped: Dict[Tuple[str, str], List[SchemaRelationship]] = {}
    for rel in filtered:
        key = (rel.source_schema, rel.target_schema)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(rel)
    
    # Consolidate each group
    consolidated = []
    for (source, target), group in grouped.items():
        if len(group) == 1:
            # Only one relationship, keep as is
            consolidated.append(group[0])
        else:
            # Multiple relationships, consolidate
            consolidated.append(_merge_relationships(group))
    
    # Sort by confidence score (highest first)
    consolidated.sort(key=lambda r: r.confidence.score, reverse=True)
    
    return consolidated


def _merge_relationships(relationships: List[SchemaRelationship]) -> SchemaRelationship:
    """
    Merge multiple relationships between the same schemas.
    
    Args:
        relationships: List of relationships to merge.
        
    Returns:
        SchemaRelationship: Merged relationship.
    """
    # Select the highest confidence relationship as base
    base = max(relationships, key=lambda r: r.confidence.score)
    
    # Collect all confidence factors
    all_factors: Dict[str, List[float]] = {}
    for rel in relationships:
        for factor, value in rel.confidence.factors.items():
            if factor not in all_factors:
                all_factors[factor] = []
            all_factors[factor].append(value)
    
    # Average the factors
    merged_factors = {factor: sum(values) / len(values) 
                     for factor, values in all_factors.items()}
    
    # Add a "multiple_signals" boost if multiple detection methods were used
    detection_methods = {rel.confidence.detection_method for rel in relationships}
    if len(detection_methods) > 1:
        merged_factors["multiple_signals"] = 0.1 * min(len(detection_methods), 3)
    
    # Create merged confidence
    merged_confidence = calculate_confidence(
        factors=merged_factors,
        detection_method=", ".join(sorted(detection_methods)),
        rationale=f"Merged from {len(relationships)} relationship detections"
    )
    
    # Create merged metadata
    merged_metadata = {
        **base.metadata,
        "merged_from": len(relationships),
        "original_methods": list(detection_methods),
    }
    
    # Create merged relationship
    return SchemaRelationship(
        source_schema=base.source_schema,
        target_schema=base.target_schema,
        source_fields=base.source_fields,
        target_fields=base.target_fields,
        relationship_type=base.relationship_type,
        confidence=merged_confidence,
        bidirectional=base.bidirectional,
        metadata=merged_metadata,
    )
