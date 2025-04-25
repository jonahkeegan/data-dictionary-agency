"""
Utility modules for relationship detection.

This package contains utility modules for comparing schemas, calculating confidence scores,
and consolidating relationships.
"""

# Import key utility functions for easier access
from src.relationship_detection.utils.comparators import (
    are_types_compatible,
    compare_schemas,
    compute_name_similarity,
    get_schema_id,
    is_id_field,
)

from src.relationship_detection.utils.confidence import (
    calculate_confidence,
    consolidate_relationships,
    validate_relationship_type,
)

from src.relationship_detection.utils.consolidation import (
    create_schema_coverage_map,
    create_relationship_store,
    filter_relationships_by_confidence,
    filter_relationships_by_type,
)
