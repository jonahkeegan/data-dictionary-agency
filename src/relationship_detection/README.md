# Relationship Detection Module

This module provides functionality for detecting and analyzing relationships between schemas. It uses various strategies to identify different types of relationships such as one-to-one, one-to-many, many-to-one, and many-to-many relationships between schemas.

## Overview

The relationship detection system employs a layered approach:

1. **Core Service Layer**: Coordinates the detection process using multiple strategies
2. **Strategy Layer**: Multiple detection strategies with different approaches
3. **Utility Layer**: Helper functions for confidence calculation and relationship consolidation
4. **Model Layer**: Data models for representing relationships and their metadata

## Components

### Core Service

- `RelationshipDetectionService`: Main entry point that orchestrates relationship detection

### Strategies

Multiple strategies are implemented for identifying relationships:

- `ForeignKeyRelationshipStrategy`: Detects relationships based on explicit foreign key definitions
- `NameBasedRelationshipStrategy`: Detects relationships by analyzing field naming patterns
- `StructuralSimilarityStrategy`: Detects relationships based on structural similarity between schemas

### Utility Functions

- `comparators`: Utility functions for comparing schemas and fields
- `confidence`: Functions for calculating and manipulating confidence scores
- `consolidation`: Functions for consolidating and managing relationships

### Models

- `RelationshipType`: Enum representing different types of relationships
- `RelationshipConfidence`: Model for confidence information about a relationship
- `SchemaRelationship`: Model representing a relationship between two schemas
- `SchemaRelationshipStore`: Storage model for schema relationships

## Usage

```python
from src.format_detection.models import SchemaDetails
from src.relationship_detection.service import RelationshipDetectionService

# Create the service
service = RelationshipDetectionService()

# Prepare schema details from your data sources
schemas: List[SchemaDetails] = [...]  # Your schema objects

# Configure detection options (optional)
options = {
    "confidence_threshold": 0.6,  # Minimum confidence threshold (default: 0.5)
    "max_relationships": 1000,    # Maximum number of relationships to return
    "enhance_types": True         # Use type inference to enhance schema types
}

# Detect relationships
relationship_store = await service.detect_relationships(schemas, options)

# Access detected relationships
relationships = relationship_store.relationships

# Access schema coverage information
coverage = relationship_store.schema_coverage

# Get confidence summary
confidence_summary = relationship_store.confidence_summary

# Access additional metadata
metadata = relationship_store.metadata
```

## Extending

### Adding a Custom Detection Strategy

To add a custom detection strategy:

1. Extend the `RelationshipStrategy` abstract base class
2. Implement the required methods: `detect()` and `get_priority()`
3. Register your strategy with the service:

```python
from src.relationship_detection.service import RelationshipDetectionService
from src.relationship_detection.strategies.base import RelationshipStrategy
from src.format_detection.models import SchemaDetails
from src.relationship_detection.models import SchemaRelationship

class CustomRelationshipStrategy(RelationshipStrategy):
    def detect(self, schemas: List[SchemaDetails], options: Optional[Dict[str, Any]] = None) -> List[SchemaRelationship]:
        # Implement your detection logic
        relationships = []
        # ...
        return relationships
        
    def get_priority(self) -> int:
        # Set priority (lower values run first)
        return 50

# Register with service
service = RelationshipDetectionService()
service.register_strategy(CustomRelationshipStrategy())
```

## Key Features

- Layered detection system with multiple strategies
- Confidence scoring for relationships
- Consolidation of duplicate relationships
- Extensible architecture for adding custom strategies
- Integration with schema enhancement via type inference
- Comprehensive metadata for relationships and coverage
