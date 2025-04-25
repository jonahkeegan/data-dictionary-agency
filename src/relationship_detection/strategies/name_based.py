"""
Name-based relationship detection strategy.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Pattern

from src.format_detection.models import DataType, SchemaDetails
from src.relationship_detection.models import (
    RelationshipConfidence,
    RelationshipType,
    SchemaRelationship,
)
from src.relationship_detection.strategies.base import RelationshipStrategy


logger = logging.getLogger(__name__)


class NameBasedRelationshipStrategy(RelationshipStrategy):
    """
    Relationship detection based on field naming patterns.
    
    This strategy detects relationships by analyzing field names across schemas
    to identify common naming patterns that suggest relationships (e.g., "user_id"
    in a "comments" table suggesting a relationship to the "id" field in a "users" table).
    """
    
    def __init__(self):
        """Initialize the name-based relationship detection strategy."""
        # Compile patterns for foreign key naming conventions
        self.foreign_key_patterns = self._compile_foreign_key_patterns()
        
        # Compile patterns for plural/singular form matching
        self.plural_patterns = self._compile_plural_patterns()
        
        # Common ID field names
        self.common_id_fields = {"id", "uuid", "key", "code"}
        
        # Pattern for ID field detection
        self.id_field_pattern = re.compile(r"^(id|uuid|key|code)$", re.IGNORECASE)
        
    def detect(self, schemas: List[SchemaDetails], options: Optional[Dict[str, Any]] = None) -> List[SchemaRelationship]:
        """
        Detect relationships based on naming patterns.
        
        Args:
            schemas: List of schema details to analyze.
            options: Optional detection options.
            
        Returns:
            List[SchemaRelationship]: Detected relationships.
        """
        logger.info("Detecting name-based relationships among %d schemas", len(schemas))
        
        # Apply options
        options = options or {}
        min_confidence = options.get("min_confidence", 0.5)
        
        # Create schema lookup by ID
        schema_lookup = {self._get_schema_id(schema): schema for schema in schemas}
        
        # Create field index for fast lookups
        field_index = self._build_field_index(schemas)
        
        # Collect potential relationships
        potential_relationships: List[Tuple[str, str, List[str], List[str], float, Dict[str, Any]]] = []
        
        # Process each schema to find potential relationships
        for schema in schemas:
            schema_id = self._get_schema_id(schema)
            schema_singular = self._get_singular_form(schema_id)
            
            # Check each field for name-based relationship patterns
            for field in schema.fields:
                # Skip non-ID-like fields for FK lookup
                if not self._is_potential_foreign_key(field.name):
                    continue
                
                # Extract potential target from field name
                target_info = self._extract_target_from_field_name(field.name, schema_id)
                if not target_info:
                    continue
                
                target_schema_name, target_confidence = target_info
                
                # Skip self-references unless they look intentional
                if target_schema_name == schema_id and not self._is_explicit_self_reference(field.name):
                    continue
                
                # Look for matching target schema
                target_schema = None
                for potential_match in self._find_schema_matches(target_schema_name, schema_lookup):
                    target_schema = schema_lookup.get(potential_match)
                    if target_schema:
                        # See if the target schema has ID fields
                        target_fields = self._find_id_fields(target_schema)
                        if target_fields:
                            # We found a potential relationship
                            confidence_boost = 0.1 if potential_match == target_schema_name else 0.0
                            relationship_confidence = target_confidence + confidence_boost
                            
                            # Add the potential relationship
                            potential_relationships.append((
                                schema_id,                # source schema
                                potential_match,         # target schema
                                [field.name],            # source fields
                                target_fields,           # target fields
                                relationship_confidence, # confidence
                                {                        # metadata
                                    "detected_by": "name_pattern",
                                    "field_pattern": field.name,
                                    "target_match": potential_match
                                }
                            ))
            
            # Check for reverse relationships where the schema name is used in other schemas
            for other_schema_id, other_schema in schema_lookup.items():
                if other_schema_id == schema_id:
                    continue
                
                # Check if any field in other schema references this schema by name
                for other_field in other_schema.fields:
                    # Check if field name contains this schema's name
                    if self._field_references_schema(other_field.name, schema_id, schema_singular):
                        # This field might be referencing our schema
                        target_fields = self._find_id_fields(schema)
                        if target_fields:
                            # We found a potential reverse relationship
                            relationship_confidence = 0.6  # Base confidence for this pattern
                            
                            # Add the potential relationship
                            potential_relationships.append((
                                other_schema_id,         # source schema
                                schema_id,               # target schema
                                [other_field.name],      # source fields
                                target_fields,           # target fields 
                                relationship_confidence, # confidence
                                {                        # metadata
                                    "detected_by": "schema_reference",
                                    "field_reference": other_field.name,
                                    "pattern_match": schema_singular
                                }
                            ))
        
        # Convert potential relationships to actual relationships
        relationships = self._create_relationships(potential_relationships, schema_lookup, min_confidence)
        
        logger.info("Detected %d name-based relationships", len(relationships))
        return relationships
    
    def get_priority(self) -> int:
        """
        Get priority of this strategy.
        
        Returns:
            int: Priority (lower = higher priority).
        """
        return 20  # Medium priority, after foreign key strategy
    
    def _compile_foreign_key_patterns(self) -> List[Tuple[Pattern, float]]:
        """
        Compile regex patterns for foreign key naming conventions.
        
        Returns:
            List[Tuple[Pattern, float]]: List of (pattern, confidence) tuples.
        """
        patterns = [
            # Exact match pattern: <table>_id 
            (re.compile(r"^([a-z0-9_]+)_id$", re.IGNORECASE), 0.7),
            
            # Suffix pattern: <table>id 
            (re.compile(r"^([a-z0-9_]+)id$", re.IGNORECASE), 0.65),
            
            # FK pattern: fk_<table>
            (re.compile(r"^fk_([a-z0-9_]+)$", re.IGNORECASE), 0.75),
            
            # Ref pattern: <table>_ref
            (re.compile(r"^([a-z0-9_]+)_ref$", re.IGNORECASE), 0.6),
            
            # Reference pattern: <table>_reference
            (re.compile(r"^([a-z0-9_]+)_reference$", re.IGNORECASE), 0.65),
            
            # UUID pattern: <table>_uuid
            (re.compile(r"^([a-z0-9_]+)_uuid$", re.IGNORECASE), 0.7),
            
            # Key pattern: <table>_key
            (re.compile(r"^([a-z0-9_]+)_key$", re.IGNORECASE), 0.65),
            
            # Simple pattern: <table>
            (re.compile(r"^([a-z0-9_]+)$", re.IGNORECASE), 0.3),
        ]
        return patterns
    
    def _compile_plural_patterns(self) -> List[Tuple[Pattern, str]]:
        """
        Compile regex patterns for plural/singular form matching.
        
        Returns:
            List[Tuple[Pattern, str]]: List of (pattern, replacement) tuples.
        """
        patterns = [
            # Regular plurals: add 's'
            (re.compile(r"s$"), ""),
            
            # Plurals ending in 'ies': replace with 'y'
            (re.compile(r"ies$"), "y"),
            
            # Plurals ending in 'es': remove 'es'
            (re.compile(r"es$"), ""),
            
            # Special cases
            (re.compile(r"children$"), "child"),
            (re.compile(r"people$"), "person"),
        ]
        return patterns
    
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
    
    def _is_potential_foreign_key(self, field_name: str) -> bool:
        """
        Check if a field name matches common foreign key naming patterns.
        
        Args:
            field_name: Field name to check.
            
        Returns:
            bool: True if field name matches foreign key patterns.
        """
        # Check common foreign key patterns
        if field_name.endswith("_id") or field_name.endswith("Id"):
            return True
            
        if field_name.endswith("_key") or field_name.endswith("Key"):
            return True
            
        if field_name.endswith("_ref") or field_name.endswith("Ref"):
            return True
            
        if field_name.startswith("fk_") or field_name.startswith("FK_"):
            return True
            
        # Check if field name is simply another table name
        if len(field_name) > 2 and "_" not in field_name and field_name.islower():
            return True
            
        return False
    
    def _extract_target_from_field_name(self, field_name: str, source_schema_id: str) -> Optional[Tuple[str, float]]:
        """
        Extract potential target schema name from field name.
        
        Args:
            field_name: Field name to analyze.
            source_schema_id: ID of the source schema.
            
        Returns:
            Optional[Tuple[str, float]]: Tuple of (target_schema_name, confidence) if found.
        """
        # Try each pattern
        for pattern, confidence in self.foreign_key_patterns:
            match = pattern.match(field_name)
            if match:
                target_name = match.group(1).lower()
                
                # Ignore common false positives
                if target_name in {"primary", "foreign", "unique", "created", "updated", "parent"}:
                    continue
                
                # Ignore self-references unless explicitly named
                if target_name == source_schema_id.lower() and not field_name.endswith("_parent_id"):
                    continue
                
                return target_name, confidence
        
        return None
    
    def _is_explicit_self_reference(self, field_name: str) -> bool:
        """
        Check if a field name explicitly indicates a self-reference.
        
        Args:
            field_name: Field name to check.
            
        Returns:
            bool: True if field name indicates a self-reference.
        """
        self_ref_indicators = {"parent", "self", "parent_id", "self_ref"}
        return any(indicator in field_name.lower() for indicator in self_ref_indicators)
    
    def _get_singular_form(self, name: str) -> str:
        """
        Get singular form of a name that might be plural.
        
        Args:
            name: Name to convert to singular form.
            
        Returns:
            str: Singular form of the name.
        """
        name_lower = name.lower()
        
        # Try each pattern
        for pattern, replacement in self.plural_patterns:
            if pattern.search(name_lower):
                singular = pattern.sub(replacement, name_lower)
                # Only return if actually changed and not too short
                if singular != name_lower and len(singular) > 2:
                    return singular
        
        return name_lower
    
    def _find_schema_matches(self, target_name: str, schema_lookup: Dict[str, SchemaDetails]) -> List[str]:
        """
        Find schemas that match the target name.
        
        Args:
            target_name: Target schema name to match.
            schema_lookup: Dictionary of schema_id -> schema.
            
        Returns:
            List[str]: List of matching schema IDs.
        """
        matches = []
        target_singular = self._get_singular_form(target_name)
        
        for schema_id in schema_lookup:
            schema_id_lower = schema_id.lower()
            schema_singular = self._get_singular_form(schema_id)
            
            # Exact match
            if schema_id_lower == target_name:
                matches.append(schema_id)
                continue
            
            # Singular match
            if schema_singular == target_singular:
                matches.append(schema_id)
                continue
            
            # Plural match
            if schema_id_lower == target_singular + "s":
                matches.append(schema_id)
                continue
            
            # Partial match (only for longer names)
            if len(target_name) > 3 and len(schema_id_lower) > 3:
                if target_name in schema_id_lower or schema_id_lower in target_name:
                    matches.append(schema_id)
                    continue
        
        return matches
    
    def _find_id_fields(self, schema: SchemaDetails) -> List[str]:
        """
        Find ID fields in a schema.
        
        Args:
            schema: Schema details.
            
        Returns:
            List[str]: List of ID field names.
        """
        # Start with primary keys
        if schema.primary_keys:
            return schema.primary_keys
        
        # Look for common ID fields
        id_fields = []
        for field in schema.fields:
            # Check exact matches for common ID field names
            if field.name.lower() in self.common_id_fields:
                id_fields.append(field.name)
                continue
            
            # Check pattern match
            if self.id_field_pattern.match(field.name):
                id_fields.append(field.name)
                continue
            
            # Check field metadata and type
            if field.metadata.get("primary_key") or field.metadata.get("is_primary_key"):
                id_fields.append(field.name)
                continue
                
            # Check for unique fields
            if field.metadata.get("unique") and field.data_type in {DataType.INTEGER, DataType.STRING, DataType.UUID}:
                id_fields.append(field.name)
                continue
        
        return id_fields
    
    def _field_references_schema(self, field_name: str, schema_id: str, schema_singular: str) -> bool:
        """
        Check if a field name references a schema by name.
        
        Args:
            field_name: Field name to check.
            schema_id: Schema ID to look for.
            schema_singular: Singular form of schema ID.
            
        Returns:
            bool: True if field name references the schema.
        """
        field_lower = field_name.lower()
        schema_lower = schema_id.lower()
        
        # Check common foreign key patterns
        if f"{schema_singular}_id" == field_lower or f"{schema_lower}_id" == field_lower:
            return True
            
        if field_lower.startswith(f"{schema_singular}_") or field_lower.startswith(f"{schema_lower}_"):
            return True
            
        if field_lower.endswith(f"_{schema_singular}") or field_lower.endswith(f"_{schema_lower}"):
            return True
            
        if f"{schema_singular}id" == field_lower or f"{schema_lower}id" == field_lower:
            return True
            
        return False
    
    def _build_field_index(self, schemas: List[SchemaDetails]) -> Dict[str, Dict[str, List[str]]]:
        """
        Build index of field names across schemas for fast lookups.
        
        Args:
            schemas: List of schema details.
            
        Returns:
            Dict[str, Dict[str, List[str]]]: Index of field names.
        """
        index: Dict[str, Dict[str, List[str]]] = {}
        
        for schema in schemas:
            schema_id = self._get_schema_id(schema)
            
            for field in schema.fields:
                field_lower = field.name.lower()
                
                if field_lower not in index:
                    index[field_lower] = {}
                    
                if schema_id not in index[field_lower]:
                    index[field_lower][schema_id] = []
                    
                index[field_lower][schema_id].append(field.name)
        
        return index
    
    def _create_relationships(
        self,
        potential_relationships: List[Tuple[str, str, List[str], List[str], float, Dict[str, Any]]],
        schema_lookup: Dict[str, SchemaDetails],
        min_confidence: float
    ) -> List[SchemaRelationship]:
        """
        Convert potential relationships to actual relationships.
        
        Args:
            potential_relationships: List of potential relationships.
            schema_lookup: Dictionary of schema_id -> schema.
            min_confidence: Minimum confidence threshold.
            
        Returns:
            List[SchemaRelationship]: List of relationships.
        """
        relationships = []
        
        # Process each potential relationship
        for source_id, target_id, source_fields, target_fields, base_confidence, metadata in potential_relationships:
            # Skip if source or target schema is not in lookup
            if source_id not in schema_lookup or target_id not in schema_lookup:
                continue
            
            # Get schemas
            source_schema = schema_lookup[source_id]
            target_schema = schema_lookup[target_id]
            
            # Adjust confidence based on schema and field metadata
            confidence_factors = {"base_confidence": base_confidence}
            
            # Check if source field is explicitly marked as foreign key
            for field_name in source_fields:
                field = next((f for f in source_schema.fields if f.name == field_name), None)
                if field:
                    if field.metadata.get("foreign_key") or field.metadata.get("references"):
                        confidence_factors["explicit_fk_metadata"] = 0.2
                        
                    # Check if field type matches target field type
                    target_field = next((f for f in target_schema.fields if f.name in target_fields), None)
                    if target_field and field.data_type == target_field.data_type:
                        confidence_factors["type_match"] = 0.1
            
            # Check for naming pattern quality
            if metadata.get("detected_by") == "name_pattern":
                field_pattern = metadata.get("field_pattern", "")
                if "_" in field_pattern:
                    confidence_factors["clear_naming_pattern"] = 0.05
                    
                if target_id.lower() in field_pattern.lower():
                    confidence_factors["direct_name_reference"] = 0.1
            
            # Calculate adjusted confidence
            confidence_score = sum(confidence_factors.values())
            confidence_score = max(0.1, min(0.9, confidence_score))  # Cap between 0.1 and 0.9
            
            # Skip if below threshold
            if confidence_score < min_confidence:
                continue
            
            # Determine relationship type
            rel_type = self._determine_relationship_type(
                source_schema, target_schema, source_fields, target_fields)
            
            # Create confidence object
            confidence = RelationshipConfidence(
                score=confidence_score,
                factors=confidence_factors,
                rationale=self._generate_rationale(source_id, target_id, source_fields, metadata),
                detection_method="name_pattern_analysis",
            )
            
            # Create relationship
            relationship = SchemaRelationship(
                source_schema=source_id,
                target_schema=target_id,
                source_fields=source_fields,
                target_fields=target_fields,
                relationship_type=rel_type,
                confidence=confidence,
                bidirectional=False,
                metadata=metadata,
            )
            
            relationships.append(relationship)
        
        return relationships
    
    def _determine_relationship_type(
        self, 
        source_schema: SchemaDetails, 
        target_schema: SchemaDetails,
        source_fields: List[str],
        target_fields: List[str]
    ) -> RelationshipType:
        """
        Determine the type of relationship based on schema metadata.
        
        Args:
            source_schema: Source schema details.
            target_schema: Target schema details.
            source_fields: Source field names.
            target_fields: Target field names.
            
        Returns:
            RelationshipType: Relationship type.
        """
        # Check if source fields are unique
        source_is_unique = False
        if set(source_fields) == set(source_schema.primary_keys):
            source_is_unique = True
        else:
            for constraint in source_schema.unique_constraints:
                if set(source_fields).issubset(set(constraint)):
                    source_is_unique = True
                    break
        
        # Check if target fields are unique (usually the case for referenced fields)
        target_is_unique = False
        if set(target_fields) == set(target_schema.primary_keys):
            target_is_unique = True
        else:
            for constraint in target_schema.unique_constraints:
                if set(target_fields).issubset(set(constraint)):
                    target_is_unique = True
                    break
        
        # Determine relationship cardinality
        if source_is_unique and target_is_unique:
            # Both sides have unique constraints
            return RelationshipType.ONE_TO_ONE
        elif source_is_unique and not target_is_unique:
            # Only source side has unique constraint
            return RelationshipType.ONE_TO_MANY
        elif not source_is_unique and target_is_unique:
            # Only target side has unique constraint (most common for FKs)
            return RelationshipType.MANY_TO_ONE
        else:
            # Neither side has unique constraint (unusual for direct relationship)
            return RelationshipType.MANY_TO_MANY
    
    def _generate_rationale(
        self, 
        source_id: str, 
        target_id: str, 
        source_fields: List[str],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate rationale for the relationship detection.
        
        Args:
            source_id: Source schema ID.
            target_id: Target schema ID.
            source_fields: Source field names.
            metadata: Relationship metadata.
            
        Returns:
            str: Rationale for the relationship.
        """
        detected_by = metadata.get("detected_by", "")
        
        if detected_by == "name_pattern":
            field_pattern = metadata.get("field_pattern", source_fields[0])
            return f"Field '{field_pattern}' in '{source_id}' matched naming pattern for '{target_id}'"
        elif detected_by == "schema_reference":
            field_reference = metadata.get("field_reference", source_fields[0])
            pattern_match = metadata.get("pattern_match", "")
            return f"Field '{field_reference}' in '{source_id}' contains reference to '{pattern_match}' in '{target_id}'"
        else:
            return f"Name-based relationship detected between '{source_id}' and '{target_id}'"
