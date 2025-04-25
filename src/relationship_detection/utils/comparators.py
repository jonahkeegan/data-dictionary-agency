"""
Utility functions for comparing schema fields and structures.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, Union

from src.format_detection.models import DataType, FieldInfo, SchemaDetails
from src.format_detection.type_inference.models import EnhancedTypeInfo, TypePattern


logger = logging.getLogger(__name__)


def are_types_compatible(type1: DataType, type2: DataType) -> bool:
    """
    Check if two data types are compatible.
    
    Args:
        type1: First data type.
        type2: Second data type.
        
    Returns:
        bool: True if types are compatible.
    """
    # If same type, they are compatible
    if type1 == type2:
        return True
    
    # Check compatible pairs
    compatible_pairs = {
        (DataType.INTEGER, DataType.FLOAT),
        (DataType.STRING, DataType.ENUM),
        (DataType.STRING, DataType.UUID),
        (DataType.STRING, DataType.DATE),
        (DataType.STRING, DataType.DATETIME),
        (DataType.DATE, DataType.DATETIME),
        (DataType.OBJECT, DataType.ARRAY),  # In some formats, these can be interchangeable
    }
    
    pair = (type1, type2)
    reverse_pair = (type2, type1)
    
    return pair in compatible_pairs or reverse_pair in compatible_pairs


def are_field_types_compatible(
    field1: FieldInfo, 
    field2: FieldInfo,
    check_enhanced_types: bool = True
) -> Tuple[bool, float]:
    """
    Check if two fields have compatible types and calculate compatibility score.
    
    Args:
        field1: First field information.
        field2: Second field information.
        check_enhanced_types: Whether to check enhanced type information.
        
    Returns:
        Tuple[bool, float]: (is_compatible, compatibility_score)
    """
    # If exactly the same type, they are compatible with perfect score
    if field1.data_type == field2.data_type:
        return True, 1.0
    
    # Check basic type compatibility
    if are_types_compatible(field1.data_type, field2.data_type):
        return True, 0.7
    
    # Check enhanced type info if requested
    if check_enhanced_types:
        enhanced_type1 = get_enhanced_type_info(field1)
        enhanced_type2 = get_enhanced_type_info(field2)
        
        if enhanced_type1 and enhanced_type2:
            # Check for common patterns
            patterns1 = set(enhanced_type1.patterns)
            patterns2 = set(enhanced_type2.patterns)
            common_patterns = patterns1 & patterns2
            
            if common_patterns:
                return True, 0.8
                
            # Check secondary types compatibility
            for sec_type1 in enhanced_type1.secondary_types:
                if sec_type1 == field2.data_type:
                    return True, 0.6
                for sec_type2 in enhanced_type2.secondary_types:
                    if sec_type1 == sec_type2:
                        return True, 0.5
    
    return False, 0.0


def get_enhanced_type_info(field: FieldInfo) -> Optional[EnhancedTypeInfo]:
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
            patterns = [TypePattern(p) for p in enhanced_type_dict.get("patterns", [])]
        else:
            patterns = []
            
        # Extract other fields from the enhanced type dict
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


def compute_name_similarity(name1: str, name2: str) -> float:
    """
    Compute similarity between field names.
    
    Args:
        name1: First field name.
        name2: Second field name.
        
    Returns:
        float: Similarity score between 0.0 and 1.0.
    """
    # Normalize names
    name1_norm = name1.lower().replace("_", "").replace("-", "")
    name2_norm = name2.lower().replace("_", "").replace("-", "")
    
    # If identical, maximum similarity
    if name1_norm == name2_norm:
        return 1.0
        
    # If one is a prefix or suffix of the other
    if name1_norm.startswith(name2_norm) or name2_norm.startswith(name1_norm) or \
       name1_norm.endswith(name2_norm) or name2_norm.endswith(name1_norm):
        # Calculate overlap ratio based on length
        overlap_size = min(len(name1_norm), len(name2_norm))
        max_size = max(len(name1_norm), len(name2_norm))
        return 0.6 + (0.4 * (overlap_size / max_size))
        
    # Check for partial match with significant overlap
    if len(name1_norm) >= 3 and len(name2_norm) >= 3:
        # Check for substrings with minimum length 3
        for i in range(len(name1_norm) - 2):
            substring = name1_norm[i:i+3]
            if substring in name2_norm:
                # Calculate overlap quality
                return 0.4 + (0.2 * (len(substring) / max(len(name1_norm), len(name2_norm))))
    
    # Check for character-level similarity
    common_chars = set(name1_norm) & set(name2_norm)
    if not common_chars:
        return 0.0
        
    max_length = max(len(name1_norm), len(name2_norm))
    char_similarity = len(common_chars) / max_length
    
    # Require substantial character overlap
    if char_similarity < 0.3:
        return 0.0
        
    return 0.3 * char_similarity


def compute_constraint_similarity(field1: FieldInfo, field2: FieldInfo) -> float:
    """
    Compute similarity between field constraints.
    
    Args:
        field1: First field information.
        field2: Second field information.
        
    Returns:
        float: Similarity score between 0.0 and 1.0.
    """
    # If neither has constraints, neutral similarity
    if not field1.constraints and not field2.constraints:
        return 0.5
        
    # If only one has constraints, somewhat dissimilar
    if not field1.constraints or not field2.constraints:
        return 0.2
        
    # Extract constraint types and values
    constraints1 = {(c.type, str(c.value)) for c in field1.constraints}
    constraints2 = {(c.type, str(c.value)) for c in field2.constraints}
    
    # Check for exact constraint matches
    common_constraints = constraints1 & constraints2
    if common_constraints:
        # Calculate Jaccard similarity
        union_size = len(constraints1 | constraints2)
        intersection_size = len(common_constraints)
        return 0.7 + (0.3 * (intersection_size / union_size))
    
    # If no exact matches, check for type matches with different values
    constraint_types1 = {c.type for c in field1.constraints}
    constraint_types2 = {c.type for c in field2.constraints}
    common_types = constraint_types1 & constraint_types2
    
    if common_types:
        # Calculate similarity based on type match
        union_size = len(constraint_types1 | constraint_types2)
        intersection_size = len(common_types)
        return 0.3 + (0.3 * (intersection_size / union_size))
    
    return 0.1  # Very low similarity


def get_schema_id(schema: SchemaDetails) -> str:
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


def fields_are_unique(schema: SchemaDetails, field_names: List[str]) -> bool:
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


def is_id_field(field_name: str) -> bool:
    """
    Check if a field name indicates an ID field.
    
    Args:
        field_name: Field name to check.
        
    Returns:
        bool: True if field name indicates an ID field.
    """
    # Common ID patterns
    id_patterns = [
        r"^id$",
        r"^uuid$",
        r"^key$",
        r"^code$",
        r"_id$",
        r"Id$",
        r"ID$",
        r"_key$",
        r"Key$",
        r"_uuid$",
        r"Uuid$",
        r"UUID$",
    ]
    
    # Check if the field name matches any pattern
    field_name_lower = field_name.lower()
    
    # Direct match with common ID field names
    if field_name_lower in {"id", "uuid", "key", "code", "identifier"}:
        return True
    
    # Check patterns
    for pattern in id_patterns:
        if re.search(pattern, field_name):
            return True
    
    return False


def get_singular_form(name: str) -> str:
    """
    Get singular form of a name that might be plural.
    
    Args:
        name: Name to convert to singular form.
        
    Returns:
        str: Singular form of the name.
    """
    name_lower = name.lower()
    
    # Common plural ending patterns
    patterns = [
        # Regular plurals ending in 's'
        (re.compile(r"s$"), ""),
        # Plurals ending in 'ies'
        (re.compile(r"ies$"), "y"),
        # Plurals ending in 'es'
        (re.compile(r"es$"), ""),
        # Special cases
        (re.compile(r"children$"), "child"),
        (re.compile(r"people$"), "person"),
        (re.compile(r"men$"), "man"),
        (re.compile(r"women$"), "woman"),
    ]
    
    # Try each pattern
    for pattern, replacement in patterns:
        if pattern.search(name_lower):
            singular = pattern.sub(replacement, name_lower)
            # Only return if actually changed and not too short
            if singular != name_lower and len(singular) > 2:
                return singular
    
    return name_lower


def compare_schemas(
    schema1: SchemaDetails,
    schema2: SchemaDetails,
    min_field_similarity: float = 0.6
) -> Dict[str, Any]:
    """
    Compare two schemas and calculate similarity metrics.
    
    Args:
        schema1: First schema.
        schema2: Second schema.
        min_field_similarity: Minimum similarity threshold for field matching.
        
    Returns:
        Dict[str, Any]: Schema comparison results.
    """
    schema1_id = get_schema_id(schema1)
    schema2_id = get_schema_id(schema2)
    
    # Build field maps for easier access
    fields1 = {field.name: field for field in schema1.fields}
    fields2 = {field.name: field for field in schema2.fields}
    
    # Find matching fields
    field_matches = []
    for name1, field1 in fields1.items():
        for name2, field2 in fields2.items():
            # Skip comparing ID fields with non-ID fields
            if is_id_field(name1) != is_id_field(name2):
                continue
                
            # Check type compatibility
            type_compatible, type_score = are_field_types_compatible(field1, field2)
            if not type_compatible:
                continue
                
            # Check name similarity
            name_score = compute_name_similarity(name1, name2)
            
            # Check constraint similarity
            constraint_score = compute_constraint_similarity(field1, field2)
            
            # Calculate combined similarity
            similarity = (
                0.4 * type_score +
                0.4 * name_score +
                0.2 * constraint_score
            )
            
            # If similarity is above threshold, consider it a match
            if similarity >= min_field_similarity:
                field_matches.append({
                    "field1": name1,
                    "field2": name2,
                    "similarity": similarity,
                    "type_score": type_score,
                    "name_score": name_score,
                    "constraint_score": constraint_score
                })
    
    # Calculate schema similarity metrics
    overall_similarity = 0.0
    if field_matches:
        # Average over all matches
        match_sum = sum(m["similarity"] for m in field_matches)
        overall_similarity = match_sum / len(field_matches)
    
    # Calculate coverage
    schema1_coverage = len(set(m["field1"] for m in field_matches)) / len(fields1) if fields1 else 0
    schema2_coverage = len(set(m["field2"] for m in field_matches)) / len(fields2) if fields2 else 0
    
    # Sort field matches by similarity (highest first)
    field_matches.sort(key=lambda m: m["similarity"], reverse=True)
    
    return {
        "schema1_id": schema1_id,
        "schema2_id": schema2_id,
        "field_matches": field_matches,
        "overall_similarity": overall_similarity,
        "schema1_coverage": schema1_coverage,
        "schema2_coverage": schema2_coverage,
        "match_count": len(field_matches),
    }
