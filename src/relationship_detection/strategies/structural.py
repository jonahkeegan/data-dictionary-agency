"""
Structural similarity relationship detection strategy.
"""
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from src.format_detection.models import DataType, FieldInfo, SchemaDetails
from src.format_detection.type_inference.models import TypePattern, EnhancedTypeInfo
from src.relationship_detection.models import (
    RelationshipConfidence,
    RelationshipType,
    SchemaRelationship,
)
from src.relationship_detection.strategies.base import RelationshipStrategy


logger = logging.getLogger(__name__)


class StructuralSimilarityStrategy(RelationshipStrategy):
    """
    Relationship detection based on structural similarity between schema fields.
    
    This strategy detects relationships by analyzing the structural similarity
    between fields in different schemas, considering type compatibility, field
    patterns, and constraints.
    """
    
    def detect(self, schemas: List[SchemaDetails], options: Optional[Dict[str, Any]] = None) -> List[SchemaRelationship]:
        """
        Detect relationships based on structural similarity.
        
        Args:
            schemas: List of schema details to analyze.
            options: Optional detection options.
            
        Returns:
            List[SchemaRelationship]: Detected relationships.
        """
        logger.info("Detecting structural similarity relationships among %d schemas", len(schemas))
        
        # Apply options
        options = options or {}
        min_confidence = options.get("min_confidence", 0.5)
        min_similarity = options.get("min_similarity", 0.6)
        
        # Create schema lookup by ID
        schema_lookup = {self._get_schema_id(schema): schema for schema in schemas}
        
        # Store field info by schema ID for easier access
        field_info_by_schema: Dict[str, Dict[str, FieldInfo]] = {}
        for schema in schemas:
            schema_id = self._get_schema_id(schema)
            field_info_by_schema[schema_id] = {
                field.name: field for field in schema.fields
            }
        
        # Collect relationships
        relationships: List[SchemaRelationship] = []
        
        # Process each schema pair
        processed_pairs = set()
        for i, schema1 in enumerate(schemas):
            schema1_id = self._get_schema_id(schema1)
            schema1_fields = field_info_by_schema[schema1_id]
            
            for j, schema2 in enumerate(schemas[i+1:], i+1):
                schema2_id = self._get_schema_id(schema2)
                schema2_fields = field_info_by_schema[schema2_id]
                
                # Skip self-comparison
                if schema1_id == schema2_id:
                    continue
                
                # Create a unique pair ID to avoid duplicate comparisons
                pair_id = tuple(sorted([schema1_id, schema2_id]))
                if pair_id in processed_pairs:
                    continue
                processed_pairs.add(pair_id)
                
                logger.debug("Analyzing structural similarity between %s and %s", 
                           schema1_id, schema2_id)
                
                # Find potential matching fields
                field_matches: List[Tuple[str, str, float]] = []
                
                # Compute similarity between field pairs
                for field1_name, field1 in schema1_fields.items():
                    for field2_name, field2 in schema2_fields.items():
                        # Skip comparisons between standard ID fields
                        if (self._is_standard_id_field(field1_name) and 
                            self._is_standard_id_field(field2_name)):
                            continue
                        
                        # Skip incompatible fields
                        if not self._are_types_compatible(field1, field2):
                            continue
                        
                        # Compute similarity
                        similarity = self._compute_field_similarity(field1, field2)
                        if similarity >= min_similarity:
                            field_matches.append((field1_name, field2_name, similarity))
                
                # Skip if no matches were found
                if not field_matches:
                    continue
                
                # Group matches by their similarity
                field_matches.sort(key=lambda x: x[2], reverse=True)
                grouped_matches: Dict[float, List[Tuple[str, str]]] = {}
                for field1, field2, sim in field_matches:
                    if sim not in grouped_matches:
                        grouped_matches[sim] = []
                    grouped_matches[sim].append((field1, field2))
                
                # Create a relationship for each similarity group
                for similarity, matches in grouped_matches.items():
                    if similarity < min_similarity:
                        continue
                    
                    # Extract field lists
                    schema1_fields_matched = [m[0] for m in matches]
                    schema2_fields_matched = [m[1] for m in matches]
                    
                    # Determine relationship type and direction
                    rel_info = self._determine_relationship_info(
                        schema1, schema2, 
                        schema1_fields_matched, schema2_fields_matched
                    )
                    
                    source_schema, target_schema = rel_info["source_schema"], rel_info["target_schema"]
                    source_fields, target_fields = rel_info["source_fields"], rel_info["target_fields"]
                    rel_type = rel_info["relationship_type"]
                    direction_confidence = rel_info["direction_confidence"]
                    
                    # Calculate confidence
                    confidence = self._calculate_confidence(
                        similarity, len(matches), direction_confidence, 
                        schema1, schema2, schema1_fields_matched, schema2_fields_matched
                    )
                    
                    # Skip if confidence is below threshold
                    if confidence.score < min_confidence:
                        continue
                    
                    # Create relationship
                    relationship = SchemaRelationship(
                        source_schema=source_schema,
                        target_schema=target_schema,
                        source_fields=source_fields,
                        target_fields=target_fields,
                        relationship_type=rel_type,
                        confidence=confidence,
                        bidirectional=rel_info["bidirectional"],
                        metadata={
                            "similarity_score": similarity,
                            "matches": len(matches),
                            "detection_method": "structural_similarity",
                            "field_matches": [
                                {"source": m[0], "target": m[1]} for m in matches
                            ],
                        }
                    )
                    
                    relationships.append(relationship)
                    logger.debug("Detected structural relationship: %s <-> %s (similarity: %.2f)", 
                               source_schema, target_schema, similarity)
        
        logger.info("Detected %d structural similarity relationships", len(relationships))
        return relationships
    
    def get_priority(self) -> int:
        """
        Get priority of this strategy.
        
        Returns:
            int: Priority (lower = higher priority).
        """
        return 30  # Lower priority, run after name-based strategy
    
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
    
    def _is_standard_id_field(self, field_name: str) -> bool:
        """
        Check if a field is a standard ID field.
        
        Args:
            field_name: Field name to check.
            
        Returns:
            bool: True if field is a standard ID field.
        """
        std_id_patterns = {"id", "uuid", "key", "code"}
        field_lower = field_name.lower()
        
        return field_lower in std_id_patterns or field_lower == "id"
    
    def _are_types_compatible(self, field1: FieldInfo, field2: FieldInfo) -> bool:
        """
        Check if two fields have compatible types.
        
        Args:
            field1: First field information.
            field2: Second field information.
            
        Returns:
            bool: True if fields have compatible types.
        """
        # If exactly the same type, they are compatible
        if field1.data_type == field2.data_type:
            return True
        
        # Check for compatible pairs
        compatible_pairs = {
            (DataType.INTEGER, DataType.FLOAT),
            (DataType.STRING, DataType.ENUM),
            (DataType.STRING, DataType.UUID),
            (DataType.STRING, DataType.DATE),
            (DataType.STRING, DataType.DATETIME),
            (DataType.DATE, DataType.DATETIME),
        }
        
        pair = (field1.data_type, field2.data_type)
        reverse_pair = (field2.data_type, field1.data_type)
        
        if pair in compatible_pairs or reverse_pair in compatible_pairs:
            return True
            
        # Special case: check for enhanced type info
        enhanced_type1 = self._get_enhanced_type_info(field1)
        enhanced_type2 = self._get_enhanced_type_info(field2)
        
        if enhanced_type1 and enhanced_type2:
            # Check for common patterns
            for pattern in enhanced_type1.patterns:
                if pattern in enhanced_type2.patterns:
                    return True
        
        return False
    
    def _get_enhanced_type_info(self, field: FieldInfo) -> Optional[EnhancedTypeInfo]:
        """
        Get enhanced type information from field metadata.
        
        Args:
            field: Field information.
            
        Returns:
            Optional[EnhancedTypeInfo]: Enhanced type information if available.
        """
        if not field.metadata or "enhanced_type" not in field.metadata:
            return None
            
        try:
            # Convert dict to EnhancedTypeInfo
            enhanced_type_dict = field.metadata["enhanced_type"]
            
            # Simplistic conversion - in a real system we'd use proper deserialization
            if "patterns" in enhanced_type_dict:
                patterns = [TypePattern(p) for p in enhanced_type_dict["patterns"]]
            else:
                patterns = []
                
            return EnhancedTypeInfo(
                primary_type=enhanced_type_dict.get("primary_type", field.data_type),
                secondary_types=enhanced_type_dict.get("secondary_types", []),
                patterns=patterns,
                confidence=enhanced_type_dict.get("confidence", {"score": 0.5}),
                format_specific_type=enhanced_type_dict.get("format_specific_type", None),
                possible_alternatives=enhanced_type_dict.get("possible_alternatives", []),
                constraints=enhanced_type_dict.get("constraints", []),
                metadata=enhanced_type_dict.get("metadata", {})
            )
        except Exception as e:
            logger.warning("Error parsing enhanced type info: %s", str(e))
            return None
    
    def _compute_field_similarity(self, field1: FieldInfo, field2: FieldInfo) -> float:
        """
        Compute similarity between two fields.
        
        Args:
            field1: First field information.
            field2: Second field information.
            
        Returns:
            float: Similarity score between 0.0 and 1.0.
        """
        # Start with type compatibility score
        if field1.data_type == field2.data_type:
            type_score = 1.0
        elif self._are_types_compatible(field1, field2):
            type_score = 0.7
        else:
            return 0.0  # Incompatible types
        
        # Check name similarity
        name_score = self._compute_name_similarity(field1.name, field2.name)
        
        # Check constraint similarity
        constraint_score = self._compute_constraint_similarity(field1, field2)
        
        # Check pattern similarity
        pattern_score = self._compute_pattern_similarity(field1, field2)
        
        # Check sample value similarity
        sample_score = self._compute_sample_similarity(field1, field2)
        
        # Combine scores, weighted by importance
        combined_score = (
            0.35 * type_score +
            0.25 * name_score +
            0.20 * constraint_score +
            0.10 * pattern_score +
            0.10 * sample_score
        )
        
        return combined_score
    
    def _compute_name_similarity(self, name1: str, name2: str) -> float:
        """
        Compute similarity between field names.
        
        Args:
            name1: First field name.
            name2: Second field name.
            
        Returns:
            float: Similarity score between 0.0 and 1.0.
        """
        # Normalize names
        name1_norm = name1.lower().replace("_", "")
        name2_norm = name2.lower().replace("_", "")
        
        # If identical, maximum similarity
        if name1_norm == name2_norm:
            return 1.0
            
        # If one is a prefix of the other
        if name1_norm.startswith(name2_norm) or name2_norm.startswith(name1_norm):
            return 0.8
            
        # Check for significant overlap using character n-grams
        common_chars = set(name1_norm) & set(name2_norm)
        if not common_chars:
            return 0.0
            
        max_length = max(len(name1_norm), len(name2_norm))
        return len(common_chars) / max_length
    
    def _compute_constraint_similarity(self, field1: FieldInfo, field2: FieldInfo) -> float:
        """
        Compute similarity between field constraints.
        
        Args:
            field1: First field information.
            field2: Second field information.
            
        Returns:
            float: Similarity score between 0.0 and 1.0.
        """
        # If neither has constraints, they're similar in this respect
        if not field1.constraints and not field2.constraints:
            return 0.5
            
        # If only one has constraints, they're somewhat dissimilar
        if not field1.constraints or not field2.constraints:
            return 0.2
            
        # Count matching constraint types
        constraint_types1 = {c.type for c in field1.constraints}
        constraint_types2 = {c.type for c in field2.constraints}
        common_types = constraint_types1 & constraint_types2
        
        # If no common constraint types, low similarity
        if not common_types:
            return 0.3
            
        # Calculate similarity based on ratio of common constraints
        union_count = len(constraint_types1 | constraint_types2)
        intersection_count = len(common_types)
        
        return 0.3 + (0.7 * (intersection_count / union_count))
    
    def _compute_pattern_similarity(self, field1: FieldInfo, field2: FieldInfo) -> float:
        """
        Compute similarity based on enhanced type patterns.
        
        Args:
            field1: First field information.
            field2: Second field information.
            
        Returns:
            float: Similarity score between 0.0 and 1.0.
        """
        enhanced_type1 = self._get_enhanced_type_info(field1)
        enhanced_type2 = self._get_enhanced_type_info(field2)
        
        # If neither has enhanced type info, neutral score
        if not enhanced_type1 and not enhanced_type2:
            return 0.5
            
        # If only one has enhanced type info, somewhat dissimilar
        if not enhanced_type1 or not enhanced_type2:
            return 0.3
            
        # Check for common patterns
        patterns1 = set(enhanced_type1.patterns)
        patterns2 = set(enhanced_type2.patterns)
        common_patterns = patterns1 & patterns2
        
        # If they have common patterns, high similarity
        if common_patterns:
            return 0.9
            
        # If both have patterns but none in common, low similarity
        if patterns1 and patterns2:
            return 0.1
            
        # Neither has patterns, neutral
        return 0.5
    
    def _compute_sample_similarity(self, field1: FieldInfo, field2: FieldInfo) -> float:
        """
        Compute similarity based on sample values.
        
        Args:
            field1: First field information.
            field2: Second field information.
            
        Returns:
            float: Similarity score between 0.0 and 1.0.
        """
        # If neither has samples, neutral similarity
        if not field1.sample_values and not field2.sample_values:
            return 0.5
            
        # If only one has samples, somewhat dissimilar
        if not field1.sample_values or not field2.sample_values:
            return 0.3
            
        # Convert samples to strings for comparison
        samples1 = [str(s) for s in field1.sample_values if s is not None]
        samples2 = [str(s) for s in field2.sample_values if s is not None]
        
        # If either is empty after None filtering, somewhat dissimilar
        if not samples1 or not samples2:
            return 0.3
            
        # Check for identical samples
        common_samples = set(samples1) & set(samples2)
        if common_samples:
            return min(1.0, len(common_samples) / min(len(samples1), len(samples2)))
            
        # Check value pattern similarity using length distribution
        len_dist1 = {len(s) for s in samples1}
        len_dist2 = {len(s) for s in samples2}
        
        # If length distributions are similar, medium similarity
        len_similarity = len(len_dist1 & len_dist2) / max(len(len_dist1 | len_dist2), 1)
        
        return 0.3 * len_similarity
    
    def _determine_relationship_info(
        self,
        schema1: SchemaDetails,
        schema2: SchemaDetails,
        schema1_fields: List[str],
        schema2_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Determine relationship type and direction.
        
        Args:
            schema1: First schema.
            schema2: Second schema.
            schema1_fields: Fields from first schema.
            schema2_fields: Fields from second schema.
            
        Returns:
            Dict[str, Any]: Relationship information.
        """
        schema1_id = self._get_schema_id(schema1)
        schema2_id = self._get_schema_id(schema2)
        
        # Check if fields in either schema are primary keys or unique
        schema1_fields_unique = self._fields_are_unique(schema1, schema1_fields)
        schema2_fields_unique = self._fields_are_unique(schema2, schema2_fields)
        
        # Determine relationship type
        if schema1_fields_unique and schema2_fields_unique:
            rel_type = RelationshipType.ONE_TO_ONE
            bidirectional = True
            direction_confidence = 0.5  # Equal confidence for either direction
        elif schema1_fields_unique and not schema2_fields_unique:
            rel_type = RelationshipType.ONE_TO_MANY
            bidirectional = False
            direction_confidence = 0.7  # Prefer schema1 as source
        elif not schema1_fields_unique and schema2_fields_unique:
            rel_type = RelationshipType.MANY_TO_ONE
            bidirectional = False
            direction_confidence = 0.7  # Prefer schema2 as source
        else:
            # Neither set of fields is unique
            rel_type = RelationshipType.MANY_TO_MANY
            bidirectional = True
            direction_confidence = 0.5  # Equal confidence for either direction
        
        # Determine source and target based on relationship type
        if rel_type == RelationshipType.ONE_TO_MANY:
            # One-to-many: the "one" side is the source
            source_schema = schema1_id
            target_schema = schema2_id
            source_fields = schema1_fields
            target_fields = schema2_fields
        elif rel_type == RelationshipType.MANY_TO_ONE:
            # Many-to-one: the "one" side is the target
            source_schema = schema2_id
            target_schema = schema1_id
            source_fields = schema2_fields
            target_fields = schema1_fields
        else:
            # For one-to-one or many-to-many, direction is less clear
            # Choose arbitrarily (schema1 as source) or based on other factors
            source_schema = schema1_id
            target_schema = schema2_id
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
        self,
        similarity: float,
        match_count: int,
        direction_confidence: float,
        schema1: SchemaDetails,
        schema2: SchemaDetails,
        schema1_fields: List[str],
        schema2_fields: List[str]
    ) -> RelationshipConfidence:
        """
        Calculate confidence for the detected relationship.
        
        Args:
            similarity: Similarity score.
            match_count: Number of matching fields.
            direction_confidence: Confidence in relationship direction.
            schema1: First schema.
            schema2: Second schema.
            schema1_fields: Fields from first schema.
            schema2_fields: Fields from second schema.
            
        Returns:
            RelationshipConfidence: Confidence information.
        """
        # Start with similarity as base confidence
        confidence_factors = {"similarity_score": similarity}
        
        # Adjust based on number of matching fields
        field_factor = min(0.2, 0.05 * match_count)
        confidence_factors["matching_fields"] = field_factor
        
        # Adjust based on direction confidence
        confidence_factors["direction_confidence"] = direction_confidence * 0.1
        
        # Additional factor based on schema size
        schema1_size = len(schema1.fields)
        schema2_size = len(schema2.fields)
        
        # If the fields cover a significant portion of either schema
        schema1_coverage = len(schema1_fields) / schema1_size if schema1_size > 0 else 0
        schema2_coverage = len(schema2_fields) / schema2_size if schema2_size > 0 else 0
        
        max_coverage = max(schema1_coverage, schema2_coverage)
        if max_coverage > 0.5:
            confidence_factors["high_schema_coverage"] = 0.1
        
        # Calculate final confidence score (capped at 0.9 for structural similarity)
        confidence_score = sum(confidence_factors.values())
        confidence_score = min(0.9, max(0.1, confidence_score))
        
        # Generate rationale
        rationale = (
            f"Structural similarity of {similarity:.2f} between "
            f"{len(schema1_fields)} fields in schema1 and {len(schema2_fields)} fields in schema2"
        )
        
        return RelationshipConfidence(
            score=confidence_score,
            factors=confidence_factors,
            rationale=rationale,
            detection_method="structural_similarity_analysis",
        )
