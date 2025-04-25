"""
Relationship detection strategies for identifying relationships between schemas.

This package contains various strategies for detecting relationships between schemas,
each using different techniques and approaches with varying levels of priority.
"""

# Base strategy
from src.relationship_detection.strategies.base import RelationshipStrategy

# Concrete strategies
from src.relationship_detection.strategies.foreign_key import ForeignKeyRelationshipStrategy
from src.relationship_detection.strategies.name_based import NameBasedRelationshipStrategy
from src.relationship_detection.strategies.structural import StructuralSimilarityStrategy

# Export priority order for clarity
STRATEGY_PRIORITY_ORDER = [
    ForeignKeyRelationshipStrategy,
    NameBasedRelationshipStrategy,
    StructuralSimilarityStrategy,
]
