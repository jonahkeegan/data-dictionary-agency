"""
Utility functions for consolidating and managing relationships.
"""
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from src.format_detection.models import SchemaDetails
from src.relationship_detection.models import (
    RelationshipConfidence,
    RelationshipType,
    SchemaRelationship,
    SchemaRelationshipStore,
)
from src.relationship_detection.utils.confidence import (
    calculate_confidence,
    consolidate_relationships,
)
from src.relationship_detection.utils.comparators import get_schema_id


logger = logging.getLogger(__name__)


def create_schema_coverage_map(relationships: List[SchemaRelationship]) -> Dict[str, List[str]]:
    """
    Create a mapping from each schema to the schemas it relates to.
    
    Args:
        relationships: List of detected relationships.
        
    Returns:
        Dict[str, List[str]]: Mapping from schema ID to related schemas.
    """
    coverage: Dict[str, Set[str]] = {}
    
    for rel in relationships:
        source = rel.source_schema
        target = rel.target_schema
        
        # Add source -> target
        if source not in coverage:
            coverage[source] = set()
        coverage[source].add(target)
        
        # Add target -> source for bidirectional relationships
        if rel.bidirectional:
            if target not in coverage:
                coverage[target] = set()
            coverage[target].add(source)
    
    # Convert sets to sorted lists for consistent output
    return {
        schema: sorted(list(related))
        for schema, related in coverage.items()
    }


def calculate_coverage_statistics(
    relationships: List[SchemaRelationship],
    all_schemas: List[SchemaDetails]
) -> Dict[str, Any]:
    """
    Calculate statistics about schema coverage.
    
    Args:
        relationships: List of relationships.
        all_schemas: List of all schemas.
        
    Returns:
        Dict[str, Any]: Coverage statistics.
    """
    # Count unique schemas in relationships
    source_schemas = {r.source_schema for r in relationships}
    target_schemas = {r.target_schema for r in relationships}
    all_referenced_schemas = source_schemas | target_schemas
    
    # Count unique schemas in the dataset
    all_schema_ids = {get_schema_id(s) for s in all_schemas}
    
    # Calculate coverage percentage
    coverage_percentage = 0.0
    if all_schema_ids:
        coverage_percentage = len(all_referenced_schemas) / len(all_schema_ids) * 100
    
    # Calculate confidence statistics
    if relationships:
        avg_confidence = sum(r.confidence.score for r in relationships) / len(relationships)
        min_confidence = min(r.confidence.score for r in relationships)
        max_confidence = max(r.confidence.score for r in relationships)
    else:
        avg_confidence = 0.0
        min_confidence = 0.0
        max_confidence = 0.0
    
    # Count relationship types
    type_counts = {}
    for rel_type in RelationshipType:
        type_counts[rel_type.value] = sum(1 for r in relationships if r.relationship_type == rel_type)
    
    return {
        "total_schemas": len(all_schema_ids),
        "schemas_with_relationships": len(all_referenced_schemas),
        "coverage_percentage": coverage_percentage,
        "avg_confidence": avg_confidence,
        "min_confidence": min_confidence,
        "max_confidence": max_confidence,
        "relationship_type_counts": type_counts,
        "uncovered_schemas": sorted(list(all_schema_ids - all_referenced_schemas))
    }


def create_relationship_store(
    relationships: List[SchemaRelationship],
    all_schemas: List[SchemaDetails],
    options: Optional[Dict[str, Any]] = None
) -> SchemaRelationshipStore:
    """
    Create a comprehensive relationship store from detected relationships.
    
    Args:
        relationships: List of relationships.
        all_schemas: List of all schemas.
        options: Optional configuration options.
        
    Returns:
        SchemaRelationshipStore: Consolidated relationship store.
    """
    options = options or {}
    
    # Consolidate relationships
    confidence_threshold = options.get("confidence_threshold", 0.5)
    consolidated = consolidate_relationships(relationships, confidence_threshold)
    
    # Create schema coverage map
    schema_coverage = create_schema_coverage_map(consolidated)
    
    # Calculate confidence summary
    confidence_summary = {
        "mean": sum(r.confidence.score for r in consolidated) / len(consolidated) if consolidated else 0.0,
        "min": min(r.confidence.score for r in consolidated) if consolidated else 0.0,
        "max": max(r.confidence.score for r in consolidated) if consolidated else 0.0,
    }
    
    # Add confidence by type
    by_type: Dict[str, List[float]] = {}
    for rel in consolidated:
        rel_type = rel.relationship_type.value
        if rel_type not in by_type:
            by_type[rel_type] = []
        by_type[rel_type].append(rel.confidence.score)
    
    confidence_summary["by_type"] = {
        rel_type: sum(scores) / len(scores)
        for rel_type, scores in by_type.items()
    }
    
    # Calculate additional statistics
    stats = calculate_coverage_statistics(consolidated, all_schemas)
    
    # Create metadata
    metadata = {
        "total_relationships_before_consolidation": len(relationships),
        "total_relationships_after_consolidation": len(consolidated),
        "confidence_threshold": confidence_threshold,
        "coverage_statistics": stats,
        "options": options,
    }
    
    # Create relationship store
    return SchemaRelationshipStore(
        relationships=consolidated,
        schema_coverage=schema_coverage,
        confidence_summary=confidence_summary,
        metadata=metadata,
    )


def filter_relationships_by_confidence(
    relationships: List[SchemaRelationship],
    min_confidence: float = 0.5
) -> List[SchemaRelationship]:
    """
    Filter relationships by confidence score.
    
    Args:
        relationships: List of relationships.
        min_confidence: Minimum confidence threshold.
        
    Returns:
        List[SchemaRelationship]: Filtered relationships.
    """
    return [r for r in relationships if r.confidence.score >= min_confidence]


def filter_relationships_by_type(
    relationships: List[SchemaRelationship],
    relationship_types: List[RelationshipType]
) -> List[SchemaRelationship]:
    """
    Filter relationships by relationship type.
    
    Args:
        relationships: List of relationships.
        relationship_types: List of relationship types to include.
        
    Returns:
        List[SchemaRelationship]: Filtered relationships.
    """
    return [r for r in relationships if r.relationship_type in relationship_types]
