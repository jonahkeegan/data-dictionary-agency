"""
Foreign key relationship detection strategy.
"""
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from src.format_detection.models import SchemaDetails
from src.relationship_detection.models import (
    RelationshipConfidence,
    RelationshipType,
    SchemaRelationship,
)
from src.relationship_detection.strategies.base import RelationshipStrategy


logger = logging.getLogger(__name__)


class ForeignKeyRelationshipStrategy(RelationshipStrategy):
    """
    Relationship detection based on explicit foreign key definitions.
    
    This strategy detects relationships based on explicitly defined foreign keys
    in database schemas and similar structures. It has the highest confidence
    since it uses declared metadata rather than inference.
    """
    
    def detect(self, schemas: List[SchemaDetails], options: Optional[Dict[str, Any]] = None) -> List[SchemaRelationship]:
        """
        Detect relationships based on foreign key constraints.
        
        Args:
            schemas: List of schema details to analyze.
            options: Optional detection options.
            
        Returns:
            List[SchemaRelationship]: Detected relationships.
        """
        logger.info("Detecting foreign key relationships among %d schemas", len(schemas))
        
        # Apply options
        options = options or {}
        min_confidence = options.get("min_confidence", 0.7)
        
        # Create schema lookup by ID (we'll need this to resolve references)
        schema_lookup = {self._get_schema_id(schema): schema for schema in schemas}
        
        # Collect relationships
        relationships: List[SchemaRelationship] = []
        
        # Process each schema
        for schema in schemas:
            schema_id = self._get_schema_id(schema)
            
            # Skip schemas with no foreign keys
            if not schema.foreign_keys:
                continue
            
            logger.debug("Processing %d foreign keys in schema %s", 
                       len(schema.foreign_keys), schema_id)
            
            # Process each foreign key
            for fk in schema.foreign_keys:
                # Extract foreign key information
                try:
                    source_fields = self._extract_source_fields(fk)
                    target_schema_id = self._extract_target_schema(fk, schema_id)
                    target_fields = self._extract_target_fields(fk)
                    
                    # Skip if target schema not in our dataset
                    if target_schema_id not in schema_lookup:
                        logger.warning("Target schema %s not found for foreign key in %s", 
                                     target_schema_id, schema_id)
                        continue
                    
                    # Determine relationship type
                    rel_type = self._determine_relationship_type(
                        schema, schema_lookup.get(target_schema_id), source_fields, target_fields)
                    
                    # Calculate confidence
                    confidence = self._calculate_confidence(schema, fk)
                    
                    # Skip if confidence below threshold
                    if confidence.score < min_confidence:
                        continue
                    
                    # Create relationship
                    relationship = SchemaRelationship(
                        source_schema=schema_id,
                        target_schema=target_schema_id,
                        source_fields=source_fields,
                        target_fields=target_fields,
                        relationship_type=rel_type,
                        confidence=confidence,
                        bidirectional=False,  # Foreign keys are unidirectional by default
                        metadata={
                            "foreign_key_name": fk.get("name", "unnamed"),
                            "is_explicit": True,
                        }
                    )
                    
                    relationships.append(relationship)
                    logger.debug("Detected foreign key relationship: %s.%s -> %s.%s", 
                               schema_id, source_fields, target_schema_id, target_fields)
                    
                except (KeyError, ValueError) as e:
                    logger.warning("Error processing foreign key in schema %s: %s", 
                                 schema_id, str(e))
        
        logger.info("Detected %d foreign key relationships", len(relationships))
        return relationships
    
    def get_priority(self) -> int:
        """
        Get priority of this strategy.
        
        Returns:
            int: Priority (lower = higher priority).
        """
        return 10  # Highest priority since it's based on explicit metadata
    
    def _get_schema_id(self, schema: SchemaDetails) -> str:
        """
        Get a unique identifier for a schema.
        
        Args:
            schema: Schema details.
            
        Returns:
            str: Schema identifier.
        """
        # Use format-specific ID if available
        for meta_key in ["table_name", "collection_name", "class_name", "entity_name"]:
            if schema.metadata and meta_key in schema.metadata:
                return str(schema.metadata[meta_key])
        
        # Fallback to a generated ID based on fields
        if schema.fields:
            first_field = schema.fields[0].name
            return f"schema_{len(schema.fields)}_{first_field}"
        
        # Last resort
        return f"schema_{id(schema)}"
    
    def _extract_source_fields(self, foreign_key: Dict[str, Any]) -> List[str]:
        """
        Extract source fields from foreign key definition.
        
        Args:
            foreign_key: Foreign key definition.
            
        Returns:
            List[str]: Source field names.
        """
        if "source_columns" in foreign_key:
            return foreign_key["source_columns"]
        if "columns" in foreign_key:
            return foreign_key["columns"]
        if "fields" in foreign_key:
            return foreign_key["fields"]
        
        # Try to extract from composite structure
        if "column_mapping" in foreign_key:
            return list(foreign_key["column_mapping"].keys())
        
        raise ValueError("Could not determine source fields from foreign key")
    
    def _extract_target_schema(self, foreign_key: Dict[str, Any], source_schema_id: str) -> str:
        """
        Extract target schema from foreign key definition.
        
        Args:
            foreign_key: Foreign key definition.
            source_schema_id: ID of the source schema.
            
        Returns:
            str: Target schema ID.
        """
        if "referenced_table" in foreign_key:
            return foreign_key["referenced_table"]
        if "referenced_entity" in foreign_key:
            return foreign_key["referenced_entity"]
        if "target_table" in foreign_key:
            return foreign_key["target_table"]
        if "target" in foreign_key:
            return foreign_key["target"]
        if "references" in foreign_key:
            return foreign_key["references"]
        
        raise ValueError("Could not determine target schema from foreign key")
    
    def _extract_target_fields(self, foreign_key: Dict[str, Any]) -> List[str]:
        """
        Extract target fields from foreign key definition.
        
        Args:
            foreign_key: Foreign key definition.
            
        Returns:
            List[str]: Target field names.
        """
        if "referenced_columns" in foreign_key:
            return foreign_key["referenced_columns"]
        if "target_columns" in foreign_key:
            return foreign_key["target_columns"]
        if "target_fields" in foreign_key:
            return foreign_key["target_fields"]
        
        # Try to extract from composite structure
        if "column_mapping" in foreign_key:
            return list(foreign_key["column_mapping"].values())
        
        # If not specified, we'll assume target fields match source field names
        source_fields = self._extract_source_fields(foreign_key)
        
        # For simple id references, we'll assume the target field is "id"
        if len(source_fields) == 1 and source_fields[0].endswith("_id"):
            return ["id"]
        
        return source_fields
    
    def _determine_relationship_type(
        self, 
        source_schema: SchemaDetails, 
        target_schema: Optional[SchemaDetails],
        source_fields: List[str],
        target_fields: List[str]
    ) -> RelationshipType:
        """
        Determine the type of relationship based on schema metadata.
        
        Args:
            source_schema: Source schema details.
            target_schema: Target schema details (may be None if not available).
            source_fields: Source field names.
            target_fields: Target field names.
            
        Returns:
            RelationshipType: Relationship type.
        """
        # Default to many-to-one
        rel_type = RelationshipType.MANY_TO_ONE
        
        # Check if source fields are unique/primary key
        source_is_unique = self._fields_are_unique(source_schema, source_fields)
        
        # Check if target fields are unique/primary key
        target_is_unique = True  # Assume target is primary key by default
        if target_schema:
            target_is_unique = self._fields_are_unique(target_schema, target_fields)
        
        # Determine relationship type based on uniqueness
        if source_is_unique and target_is_unique:
            rel_type = RelationshipType.ONE_TO_ONE
        elif source_is_unique and not target_is_unique:
            # Unusual case: unique source pointing to non-unique target
            rel_type = RelationshipType.ONE_TO_MANY
        elif not source_is_unique and target_is_unique:
            rel_type = RelationshipType.MANY_TO_ONE
        else:
            # Both non-unique - likely a many-to-many relationship
            rel_type = RelationshipType.MANY_TO_MANY
        
        return rel_type
    
    def _fields_are_unique(self, schema: SchemaDetails, field_names: List[str]) -> bool:
        """
        Check if fields form a unique constraint in the schema.
        
        Args:
            schema: Schema details.
            field_names: Field names to check.
            
        Returns:
            bool: True if fields form a unique constraint.
        """
        # Check if fields match primary key
        if set(field_names) == set(schema.primary_keys):
            return True
        
        # Check if fields match a unique constraint
        for constraint in schema.unique_constraints:
            if set(field_names) == set(constraint):
                return True
        
        # Check if each field has a unique flag in its metadata
        fields_are_unique = True
        for name in field_names:
            field = next((f for f in schema.fields if f.name == name), None)
            if field and field.metadata.get("unique") is not True:
                fields_are_unique = False
                break
        
        if fields_are_unique and field_names:
            return True
        
        return False
    
    def _calculate_confidence(
        self, schema: SchemaDetails, foreign_key: Dict[str, Any]
    ) -> RelationshipConfidence:
        """
        Calculate confidence for a foreign key relationship.
        
        Args:
            schema: Schema details.
            foreign_key: Foreign key definition.
            
        Returns:
            RelationshipConfidence: Confidence information.
        """
        # Start with high confidence for explicit foreign keys
        base_score = 0.9
        factors = {"explicit_foreign_key": 0.9}
        
        # Adjust based on metadata quality
        meta_quality = 0.0
        
        # Check for explicit name
        if "name" in foreign_key:
            meta_quality += 0.02
            
        # Check for constraint definitions
        if "on_delete" in foreign_key or "on_update" in foreign_key:
            meta_quality += 0.02
            
        # Check for validation status
        if foreign_key.get("validated", False):
            meta_quality += 0.03
        
        if meta_quality > 0:
            factors["metadata_quality"] = meta_quality
            
        # Calculate final score (capped at 1.0)
        final_score = min(1.0, base_score + meta_quality)
        
        return RelationshipConfidence(
            score=final_score,
            factors=factors,
            rationale="Explicit foreign key definition",
            detection_method="foreign_key_analysis",
        )
