"""
Type enhancer implementations for the type inference system.
"""
import re
import logging
from abc import ABC
from datetime import datetime
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, Type, Union

from src.format_detection.models import DataType, FieldInfo
from src.format_detection.type_inference.models import (
    EnhancedTypeInfo,
    TypeAlternative,
    TypeConfidence,
    TypeConstraintEnhanced,
    TypePattern,
)
from src.format_detection.type_inference.service import TypeEnhancer


logger = logging.getLogger(__name__)


class NameBasedEnhancer(TypeEnhancer):
    """Enhances type information based on field names."""
    
    # Common name patterns for field types
    NAME_PATTERNS = {
        # String types
        DataType.STRING: [
            r".*name$", r".*title$", r".*description$", r".*text$", r".*label$", 
            r".*message$", r".*comment$", r".*address$", r".*email$"
        ],
        # ID types (still string but with special meaning)
        "id": [
            r"^id$", r"^uuid$", r".*_id$", r".*_uuid$", r"^identifier$", r".*_key$"
        ],
        # Date types
        DataType.DATE: [
            r".*date$", r".*_date$", r".*_dt$", r"^date$", r".*day$"
        ],
        # DateTime types
        DataType.DATETIME: [
            r".*timestamp$", r".*_time$", r".*datetime$", r"^time$", r"^timestamp$", 
            r".*created_at$", r".*updated_at$"
        ],
        # Boolean types
        DataType.BOOLEAN: [
            r"^is_.*$", r"^has_.*$", r"^can_.*$", r"^should_.*$", r"^allow.*$", 
            r"^enable.*$", r".*active$", r".*enabled$", r".*flag$"
        ],
        # Integer types
        DataType.INTEGER: [
            r".*count$", r".*_count$", r".*number$", r"^age$", r".*position$", 
            r"^order$", r"^index$", r".*quantity$", r".*_qty$"
        ],
        # Float types
        DataType.FLOAT: [
            r".*amount$", r".*price$", r".*cost$", r".*rate$", r".*ratio$", 
            r".*percent.*$", r".*latitude$", r".*longitude$", r".*average$", 
            r".*score$", r".*rating$"
        ],
        # Array types
        DataType.ARRAY: [
            r".*s$", r".*list$", r".*array$", r".*collection$", r".*set$", 
            r".*group$", r".*batch$"
        ],
        # Object types
        DataType.OBJECT: [
            r".*object$", r".*config$", r".*settings$", r".*options$", 
            r".*metadata$", r".*properties$", r".*attributes$"
        ],
    }
    
    def __init__(self):
        """Initialize the name-based enhancer."""
        # Compile patterns for efficiency
        self.compiled_patterns = {}
        for type_key, patterns in self.NAME_PATTERNS.items():
            self.compiled_patterns[type_key] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def enhance_type(self, field_info: FieldInfo, context: Dict[str, Any]) -> EnhancedTypeInfo:
        """
        Enhance type information based on field name.
        
        Args:
            field_info: Field information.
            context: Additional context for type inference.
            
        Returns:
            EnhancedTypeInfo: Enhanced type information.
        """
        current_type = context.get('current_type')
        if not current_type:
            raise ValueError("Current type information required in context")
        
        # Get lowercase field name for matching
        field_name = field_info.name.lower()
        
        # Check for named patterns
        for type_key, compiled_patterns in self.compiled_patterns.items():
            for pattern in compiled_patterns:
                if pattern.match(field_name):
                    confidence_boost = 0.2
                    rationale = f"Field name '{field_info.name}' matches pattern for {type_key}"
                    logger.debug(rationale)
                    
                    # If this is a special ID pattern, add ID pattern but keep string type
                    if type_key == "id":
                        current_type.patterns.append(TypePattern.ID)
                        current_type.confidence.factors["id_name_pattern"] = confidence_boost
                        current_type.confidence.rationale += f". {rationale}"
                        break
                        
                    # If inferred type differs from current, add as alternative or adjust primary
                    try:
                        inferred_type = DataType(type_key)
                        
                        if inferred_type != current_type.primary_type:
                            # Different from current - consider if we should change primary
                            
                            # Special handling for datetime vs date
                            if current_type.primary_type == DataType.STRING:
                                # String can be easily reinterpreted as another type
                                if inferred_type in (DataType.DATE, DataType.DATETIME):
                                    # Add as pattern first, don't change type immediately
                                    if inferred_type == DataType.DATE:
                                        current_type.patterns.append(TypePattern.DATE)
                                    else:
                                        current_type.patterns.append(TypePattern.DATETIME)
                                    
                                    # Add suggestion that this might be a date/datetime
                                    self._add_alternative(current_type, inferred_type, 
                                                     confidence_boost, rationale)
                                else:
                                    # For other string reconsideration
                                    self._add_alternative(current_type, inferred_type, 
                                                     confidence_boost, rationale)
                                    
                            elif inferred_type == DataType.ARRAY and field_name.endswith("s"):
                                # Plural field names suggest arrays, but don't change type outright
                                self._add_alternative(current_type, inferred_type, 
                                                 confidence_boost, rationale)
                            else:
                                # For other type conflicts, add as alternative
                                self._add_alternative(current_type, inferred_type, 
                                                 confidence_boost * 0.5, rationale)
                        else:
                            # Same as current type, boost confidence
                            current_type.confidence.factors["name_pattern_match"] = confidence_boost
                            current_type.confidence.rationale += f". {rationale}"
                            
                    except ValueError:
                        # Not a standard DataType
                        pass
                        
        return current_type

    def _add_alternative(self, current_type: EnhancedTypeInfo, 
                        alternative_type: DataType, 
                        confidence: float, 
                        rationale: str) -> None:
        """
        Add an alternative type possibility.
        
        Args:
            current_type: Current type information.
            alternative_type: Alternative data type.
            confidence: Confidence score for this alternative.
            rationale: Rationale for suggesting this alternative.
        """
        # Check if this alternative already exists
        for alt in current_type.possible_alternatives:
            if alt.type == alternative_type:
                # Already exists, increase confidence
                alt.confidence = min(0.9, alt.confidence + confidence * 0.5)
                alt.rationale += f". {rationale}"
                return
                
        # Add new alternative
        current_type.possible_alternatives.append(
            TypeAlternative(
                type=alternative_type,
                confidence=confidence,
                rationale=rationale
            )
        )
        
        # Sort alternatives by confidence (descending)
        current_type.possible_alternatives.sort(key=lambda x: x.confidence, reverse=True)
        
    def get_priority(self) -> int:
        """Get priority of this enhancer."""
        return 10  # Low priority, run first


class PatternBasedEnhancer(TypeEnhancer):
    """Enhances type information based on value patterns."""
    
    # Common regex patterns for detecting types
    VALUE_PATTERNS = {
        TypePattern.UUID: re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE
        ),
        TypePattern.EMAIL: re.compile(
            r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        ),
        TypePattern.DATE: re.compile(
            r"^(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}\.\d{2}\.\d{4})$"
        ),
        TypePattern.DATETIME: re.compile(
            r"^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}|\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}).*$"
        ),
        TypePattern.URL: re.compile(
            r"^(https?|ftp)://[^\s/$.?#].[^\s]*$"
        ),
        TypePattern.IP_ADDRESS: re.compile(
            r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4})$"
        ),
    }
    
    # Corresponding data types for patterns
    PATTERN_TYPES = {
        TypePattern.UUID: DataType.STRING,
        TypePattern.EMAIL: DataType.STRING,
        TypePattern.DATE: DataType.DATE,
        TypePattern.DATETIME: DataType.DATETIME,
        TypePattern.URL: DataType.STRING,
        TypePattern.IP_ADDRESS: DataType.STRING,
    }
    
    def enhance_type(self, field_info: FieldInfo, context: Dict[str, Any]) -> EnhancedTypeInfo:
        """
        Enhance type information based on sample values.
        
        Args:
            field_info: Field information.
            context: Additional context for type inference.
            
        Returns:
            EnhancedTypeInfo: Enhanced type information.
        """
        current_type = context.get('current_type')
        if not current_type:
            raise ValueError("Current type information required in context")
        
        # We need sample values to detect patterns
        sample_values = field_info.sample_values
        if not sample_values:
            return current_type
            
        # Check if most values match a specific pattern
        pattern_matches = {}
        
        # Check string samples for patterns
        string_samples = [str(s) for s in sample_values if s is not None]
        if not string_samples:
            return current_type
            
        # Count matches for each pattern
        for pattern_type, regex in self.VALUE_PATTERNS.items():
            matching_values = [s for s in string_samples if regex.match(s)]
            if matching_values:
                match_ratio = len(matching_values) / len(string_samples)
                pattern_matches[pattern_type] = (len(matching_values), match_ratio)
        
        # If we have strong pattern matches, enhance the type
        for pattern_type, (match_count, match_ratio) in sorted(
            pattern_matches.items(), key=lambda x: x[1][1], reverse=True
        ):
            # If more than half match a pattern, consider it significant
            if match_ratio >= 0.5:
                # Add pattern to type info
                if pattern_type not in current_type.patterns:
                    current_type.patterns.append(pattern_type)
                
                # Add confidence factor
                confidence_boost = match_ratio * 0.3  # Up to 0.3 boost for 100% match
                current_type.confidence.factors[f"{pattern_type.value}_pattern"] = confidence_boost
                
                # Maybe change the primary type based on pattern
                suggested_type = self.PATTERN_TYPES.get(pattern_type)
                if suggested_type and current_type.primary_type != suggested_type:
                    # For date/datetime patterns, consider changing type if confidence is high
                    if pattern_type in (TypePattern.DATE, TypePattern.DATETIME) and match_ratio > 0.8:
                        # If very confident, switch type
                        secondary_type = current_type.primary_type
                        current_type.primary_type = suggested_type
                        if secondary_type not in current_type.secondary_types:
                            current_type.secondary_types.append(secondary_type)
                        
                        rationale = (f"{match_ratio:.0%} of sample values match "
                                    f"{pattern_type.value} pattern")
                        current_type.confidence.rationale += f". {rationale}"
                    else:
                        # Otherwise add as alternative
                        rationale = (f"{match_ratio:.0%} of sample values match "
                                    f"{pattern_type.value} pattern")
                        self._add_alternative(current_type, suggested_type, 
                                         confidence_boost, rationale)
        
        # Special handling for heterogeneous arrays
        if current_type.primary_type == DataType.ARRAY and current_type.item_type:
            # Check if array might have heterogeneous types
            if field_info.sample_values and isinstance(field_info.sample_values[0], list):
                flat_values = [item for sublist in field_info.sample_values 
                              for item in sublist if item is not None]
                types = {type(val).__name__ for val in flat_values}
                if len(types) > 1:
                    current_type.is_heterogeneous = True
                    current_type.confidence.factors["heterogeneous_array"] = -0.1
                    current_type.confidence.rationale += ". Array contains mixed value types"
        
        return current_type
        
    def _add_alternative(self, current_type: EnhancedTypeInfo, 
                        alternative_type: DataType, 
                        confidence: float, 
                        rationale: str) -> None:
        """
        Add an alternative type possibility.
        
        Args:
            current_type: Current type information.
            alternative_type: Alternative data type.
            confidence: Confidence score for this alternative.
            rationale: Rationale for suggesting this alternative.
        """
        # Check if this alternative already exists
        for alt in current_type.possible_alternatives:
            if alt.type == alternative_type:
                # Already exists, increase confidence
                alt.confidence = min(0.9, alt.confidence + confidence * 0.5)
                alt.rationale += f". {rationale}"
                return
                
        # Add new alternative
        current_type.possible_alternatives.append(
            TypeAlternative(
                type=alternative_type,
                confidence=confidence,
                rationale=rationale
            )
        )
        
        # Sort alternatives by confidence (descending)
        current_type.possible_alternatives.sort(key=lambda x: x.confidence, reverse=True)
    
    def get_priority(self) -> int:
        """Get priority of this enhancer."""
        return 20  # Medium priority, run after name-based


class ConstraintBasedEnhancer(TypeEnhancer):
    """Enhances type information based on field constraints."""
    
    def enhance_type(self, field_info: FieldInfo, context: Dict[str, Any]) -> EnhancedTypeInfo:
        """
        Enhance type information based on field constraints.
        
        Args:
            field_info: Field information.
            context: Additional context for type inference.
            
        Returns:
            EnhancedTypeInfo: Enhanced type information.
        """
        current_type = context.get('current_type')
        if not current_type:
            raise ValueError("Current type information required in context")
        
        # Check for constraints that might inform type decisions
        constraints = field_info.constraints
        if not constraints:
            return current_type
        
        # Enhanced constraints
        enhanced_constraints = []
        
        for constraint in constraints:
            enhanced_constraint = TypeConstraintEnhanced(
                type=constraint.type,
                value=constraint.value,
                description=constraint.description,
                confidence=1.0,  # Default high confidence for explicit constraints
                source="schema"
            )
            
            enhanced_constraints.append(enhanced_constraint)
            
            # Use constraints to refine type information
            if constraint.type == "format":
                # Format constraints often indicate specific types
                format_value = str(constraint.value).lower()
                
                if format_value in ("date", "date-time", "datetime"):
                    if format_value == "date":
                        self._adjust_to_format_type(current_type, DataType.DATE, 
                                               TypePattern.DATE, "date format constraint")
                    else:
                        self._adjust_to_format_type(current_type, DataType.DATETIME, 
                                               TypePattern.DATETIME, "datetime format constraint")
                
                elif format_value in ("email", "email-address", "emailaddress"):
                    if current_type.primary_type == DataType.STRING:
                        current_type.patterns.append(TypePattern.EMAIL)
                        current_type.confidence.factors["email_format_constraint"] = 0.3
                        current_type.confidence.rationale += ". Email format constraint"
                
                elif format_value in ("uri", "url", "uri-reference"):
                    if current_type.primary_type == DataType.STRING:
                        current_type.patterns.append(TypePattern.URL)
                        current_type.confidence.factors["url_format_constraint"] = 0.3
                        current_type.confidence.rationale += ". URL format constraint"
                
                elif format_value in ("uuid", "guid"):
                    if current_type.primary_type == DataType.STRING:
                        current_type.patterns.append(TypePattern.UUID)
                        current_type.confidence.factors["uuid_format_constraint"] = 0.3
                        current_type.confidence.rationale += ". UUID format constraint"
            
            elif constraint.type == "enum":
                # Enum constraints suggest this is an enumeration type
                if isinstance(constraint.value, list) and constraint.value:
                    current_type.patterns.append(TypePattern.ENUM)
                    current_type.confidence.factors["enum_constraint"] = 0.3
                    current_type.confidence.rationale += ". Enumeration constraint"
                    
                    # Infer type from enum values if possible
                    value_types = {type(v).__name__ for v in constraint.value}
                    if len(value_types) == 1:
                        value_type = next(iter(value_types))
                        inferred_type = self._python_type_to_data_type(value_type)
                        
                        if inferred_type != current_type.primary_type:
                            self._add_alternative(current_type, inferred_type, 0.2,
                                             f"Enum values are all {value_type} type")
            
            elif constraint.type in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
                # Numeric constraints suggest this is a number
                if current_type.primary_type not in (DataType.INTEGER, DataType.FLOAT):
                    # Determine if integer or float based on constraint value
                    constraint_value = constraint.value
                    inferred_type = DataType.INTEGER if isinstance(constraint_value, int) else DataType.FLOAT
                    
                    self._add_alternative(current_type, inferred_type, 0.2,
                                     f"Numeric constraint '{constraint.type}' suggests number type")
            
            elif constraint.type in ("minLength", "maxLength", "pattern"):
                # String constraints suggest this is a string
                if current_type.primary_type != DataType.STRING:
                    self._add_alternative(current_type, DataType.STRING, 0.2,
                                     f"String constraint '{constraint.type}' suggests string type")
        
        # Update constraints with enhanced versions
        current_type.constraints = enhanced_constraints
        
        return current_type
    
    def _adjust_to_format_type(self, current_type: EnhancedTypeInfo, 
                              suggested_type: DataType,
                              pattern_type: TypePattern,
                              rationale: str) -> None:
        """
        Adjust type based on format constraint.
        
        Args:
            current_type: Current type information.
            suggested_type: Suggested data type.
            pattern_type: Pattern to add.
            rationale: Rationale for adjustment.
        """
        # Add pattern
        if pattern_type not in current_type.patterns:
            current_type.patterns.append(pattern_type)
        
        # If current type is string, consider changing it
        if current_type.primary_type == DataType.STRING:
            # If there are no conflicting signals, change type
            if not current_type.possible_alternatives:
                secondary_type = current_type.primary_type
                current_type.primary_type = suggested_type
                if secondary_type not in current_type.secondary_types:
                    current_type.secondary_types.append(secondary_type)
                
                current_type.confidence.factors[f"{pattern_type.value}_format"] = 0.3
                current_type.confidence.rationale += f". {rationale}"
            else:
                # Otherwise add as alternative
                self._add_alternative(current_type, suggested_type, 0.3, rationale)
        else:
            # Current type is not string, add as alternative
            self._add_alternative(current_type, suggested_type, 0.2, rationale)
    
    def _python_type_to_data_type(self, python_type: str) -> DataType:
        """
        Convert Python type name to DataType.
        
        Args:
            python_type: Python type name.
            
        Returns:
            DataType: Corresponding DataType.
        """
        if python_type == "str":
            return DataType.STRING
        elif python_type == "int":
            return DataType.INTEGER
        elif python_type == "float":
            return DataType.FLOAT
        elif python_type == "bool":
            return DataType.BOOLEAN
        elif python_type in ("list", "tuple"):
            return DataType.ARRAY
        elif python_type in ("dict", "OrderedDict"):
            return DataType.OBJECT
        else:
            return DataType.UNKNOWN
            
    def _add_alternative(self, current_type: EnhancedTypeInfo, 
                        alternative_type: DataType, 
                        confidence: float, 
                        rationale: str) -> None:
        """
        Add an alternative type possibility.
        
        Args:
            current_type: Current type information.
            alternative_type: Alternative data type.
            confidence: Confidence score for this alternative.
            rationale: Rationale for suggesting this alternative.
        """
        # Check if this alternative already exists
        for alt in current_type.possible_alternatives:
            if alt.type == alternative_type:
                # Already exists, increase confidence
                alt.confidence = min(0.9, alt.confidence + confidence * 0.5)
                alt.rationale += f". {rationale}"
                return
                
        # Add new alternative
        current_type.possible_alternatives.append(
            TypeAlternative(
                type=alternative_type,
                confidence=confidence,
                rationale=rationale
            )
        )
        
        # Sort alternatives by confidence (descending)
        current_type.possible_alternatives.sort(key=lambda x: x.confidence, reverse=True)
    
    def get_priority(self) -> int:
        """Get priority of this enhancer."""
        return 30  # Medium-high priority, run after pattern-based


class ComplexStructureEnhancer(TypeEnhancer):
    """Enhances type information for complex data structures."""
    
    def enhance_type(self, field_info: FieldInfo, context: Dict[str, Any]) -> EnhancedTypeInfo:
        """
        Enhance type information for complex structures.
        
        Args:
            field_info: Field information.
            context: Additional context for type inference.
            
        Returns:
            EnhancedTypeInfo: Enhanced type information.
        """
        current_type = context.get('current_type')
        if not current_type:
            raise ValueError("Current type information required in context")
        
        # Sample values are needed for analyzing complex structures
        sample_values = field_info.sample_values
        if not sample_values:
            return current_type
        
        # Handle different complex structure types
        if current_type.primary_type == DataType.ARRAY:
            return self._enhance_array_type(current_type, field_info, context)
            
        elif current_type.primary_type == DataType.OBJECT:
            return self._enhance_object_type(current_type, field_info, context)
            
        return current_type
    
    def _enhance_array_type(self, current_type: EnhancedTypeInfo, 
                           field_info: FieldInfo, 
                           context: Dict[str, Any]) -> EnhancedTypeInfo:
        """
        Enhance array type information.
        
        Args:
            current_type: Current type information.
            field_info: Field information.
            context: Additional context for type inference.
            
        Returns:
            EnhancedTypeInfo: Enhanced type information.
        """
        sample_values = field_info.sample_values
        
        # Extract array items for analysis
        item_values = []
        for sample in sample_values:
            if isinstance(sample, list):
                item_values.extend(sample)

        if not item_values:
            return current_type
            
        # Create a synthetic FieldInfo for array items
        item_field = FieldInfo(
            name=f"{field_info.name}_item",
            path=f"{field_info.path}.item",
            data_type=self._infer_item_type(item_values),
            nullable=any(v is None for v in item_values),
            description=None,
            constraints=[],
            metadata={},
            sample_values=item_values,
            statistics=None,
        )
        
        # Create empty context for item type inference
        item_context = {'field_path': item_field.path}
        
        # Create base type info for array items
        item_confidence = TypeConfidence(
            score=0.5,
            factors={"initial": 0.5},
            rationale="Based on sample array items",
            detection_method="complex_structure_analysis",
        )
        
        item_type = EnhancedTypeInfo(
            primary_type=item_field.data_type,
            secondary_types=[],
            format_specific_type=None,
            constraints=[],
            patterns=[],
            confidence=item_confidence,
            possible_alternatives=[],
            is_nullable=item_field.nullable,
            metadata={},
        )
        
        # Set item_type in current_type
        current_type.item_type = item_type
        
        # Check for heterogeneous arrays
        item_types = {type(v).__name__ for v in item_values if v is not None}
        if len(item_types) > 1:
            current_type.is_heterogeneous = True
            current_type.confidence.factors["heterogeneous_array"] = -0.1
            current_type.confidence.rationale += ". Array contains mixed value types"
        
        return current_type
    
    def _enhance_object_type(self, current_type: EnhancedTypeInfo, 
                            field_info: FieldInfo, 
                            context: Dict[str, Any]) -> EnhancedTypeInfo:
        """
        Enhance object type information.
        
        Args:
            current_type: Current type information.
            field_info: Field information.
            context: Additional context for type inference.
            
        Returns:
            EnhancedTypeInfo: Enhanced type information.
        """
        sample_values = field_info.sample_values
        
        # Extract object properties for analysis
        property_map = {}
        for sample in sample_values:
            if isinstance(sample, dict):
                for key, value in sample.items():
                    if key not in property_map:
                        property_map[key] = []
                    property_map[key].append(value)
        
        if not property_map:
            return current_type
        
        # Initialize properties dictionary
        current_type.properties = {}
        
        # Process each property
        for prop_name, prop_values in property_map.items():
            # Create a synthetic FieldInfo for property
            prop_field = FieldInfo(
                name=prop_name,
                path=f"{field_info.path}.{prop_name}",
                data_type=self._infer_item_type(prop_values),
                nullable=any(v is None for v in prop_values),
                description=None,
                constraints=[],
                metadata={},
                sample_values=prop_values,
                statistics=None,
            )
            
            # Create base type info for property
            prop_confidence = TypeConfidence(
                score=0.5,
                factors={"initial": 0.5},
                rationale="Based on sample object properties",
                detection_method="complex_structure_analysis",
            )
            
            prop_type = EnhancedTypeInfo(
                primary_type=prop_field.data_type,
                secondary_types=[],
                format_specific_type=None,
                constraints=[],
                patterns=[],
                confidence=prop_confidence,
                possible_alternatives=[],
                is_nullable=prop_field.nullable,
                metadata={},
            )
            
            # Add property type to object properties
            current_type.properties[prop_name] = prop_type
        
        # Check if this might be a map/dictionary type
        if len(property_map) >= 5:
            # Look for patterns in property names
            prop_name_types = set()
            for name in property_map.keys():
                try:
                    # Try to parse as a number
                    int(name)
                    prop_name_types.add("int")
                except ValueError:
                    try:
                        float(name)
                        prop_name_types.add("float")
                    except ValueError:
                        # Check for UUID pattern
                        uuid_pattern = re.compile(
                            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                            re.IGNORECASE
                        )
                        if uuid_pattern.match(name):
                            prop_name_types.add("uuid")
                        else:
                            prop_name_types.add("string")
            
            # If property names are all the same type (and not just 'string'), this might be a map
            if len(prop_name_types) == 1 and next(iter(prop_name_types)) != "string":
                key_type_str = next(iter(prop_name_types))
                key_type_map = {
                    "int": DataType.INTEGER,
                    "float": DataType.FLOAT,
                    "uuid": DataType.STRING
                }
                
                # Create key type information
                key_confidence = TypeConfidence(
                    score=0.7,
                    factors={"key_pattern_match": 0.7},
                    rationale=f"Map keys are consistently of type {key_type_str}",
                    detection_method="complex_structure_analysis",
                )
                
                key_type = EnhancedTypeInfo(
                    primary_type=key_type_map.get(key_type_str, DataType.STRING),
                    secondary_types=[],
                    format_specific_type=None,
                    constraints=[],
                    patterns=[TypePattern.UUID] if key_type_str == "uuid" else [],
                    confidence=key_confidence,
                    possible_alternatives=[],
                    is_nullable=False,
                    metadata={},
                )
                
                # Find most common value type
                value_type = self._get_common_value_type(property_map.values())
                
                # Mark this as potentially a map/dictionary
                current_type.key_type = key_type
                current_type.value_type = value_type
                current_type.metadata["potential_map"] = True
                current_type.confidence.factors["map_structure"] = 0.2
                current_type.confidence.rationale += ". Object structure suggests a map/dictionary"
        
        return current_type
    
    def _infer_item_type(self, values: List[Any]) -> DataType:
        """
        Infer data type from a list of values.
        
        Args:
            values: List of values to analyze.
            
        Returns:
            DataType: Inferred data type.
        """
        if not values or all(v is None for v in values):
            return DataType.UNKNOWN
        
        # Get non-null values for type detection
        non_null = [v for v in values if v is not None]
        if not non_null:
            return DataType.UNKNOWN
        
        types = {type(v) for v in non_null}
        
        # All values are of the same type
        if len(types) == 1:
            value_type = next(iter(types))
            
            if issubclass(value_type, str):
                return DataType.STRING
            elif issubclass(value_type, bool):
                return DataType.BOOLEAN
            elif issubclass(value_type, int):
                return DataType.INTEGER
            elif issubclass(value_type, float):
                return DataType.FLOAT
            elif issubclass(value_type, list):
                return DataType.ARRAY
            elif issubclass(value_type, dict):
                return DataType.OBJECT
            else:
                return DataType.UNKNOWN
        
        # Mixed types - determine most appropriate general type
        type_counts = {
            DataType.STRING: sum(1 for v in non_null if isinstance(v, str)),
            DataType.BOOLEAN: sum(1 for v in non_null if isinstance(v, bool)),
            DataType.INTEGER: sum(1 for v in non_null if isinstance(v, int) and not isinstance(v, bool)),
            DataType.FLOAT: sum(1 for v in non_null if isinstance(v, float)),
            DataType.ARRAY: sum(1 for v in non_null if isinstance(v, list)),
            DataType.OBJECT: sum(1 for v in non_null if isinstance(v, dict)),
        }
        
        # Get type with most instances
        most_common_type = max(type_counts.items(), key=lambda x: x[1])
        
        # If there's a mix of integers and floats, prefer float
        if type_counts[DataType.INTEGER] > 0 and type_counts[DataType.FLOAT] > 0:
            return DataType.FLOAT
        
        # Otherwise return the most common type
        return most_common_type[0]
    
    def _get_common_value_type(self, value_lists: List[List[Any]]) -> EnhancedTypeInfo:
        """
        Get the most common type from lists of values.
        
        Args:
            value_lists: Lists of values to analyze.
            
        Returns:
            EnhancedTypeInfo: Common type information.
        """
        # Flatten value lists
        all_values = [v for sublist in value_lists for v in sublist if v is not None]
        
        if not all_values:
            # Default to unknown if no values
            value_confidence = TypeConfidence(
                score=0.5,
                factors={"default": 0.5},
                rationale="No sample values available",
                detection_method="complex_structure_analysis",
            )
            
            return EnhancedTypeInfo(
                primary_type=DataType.UNKNOWN,
                secondary_types=[],
                format_specific_type=None,
                constraints=[],
                patterns=[],
                confidence=value_confidence,
                possible_alternatives=[],
                is_nullable=True,
                metadata={},
            )
        
        # Infer common type
        common_type = self._infer_item_type(all_values)
        
        # Create value type information
        value_confidence = TypeConfidence(
            score=0.6,
            factors={"value_analysis": 0.6},
            rationale="Based on common value type analysis",
            detection_method="complex_structure_analysis",
        )
        
        value_type = EnhancedTypeInfo(
            primary_type=common_type,
            secondary_types=[],
            format_specific_type=None,
            constraints=[],
            patterns=[],
            confidence=value_confidence,
            possible_alternatives=[],
            is_nullable=any(v is None for sublist in value_lists for v in sublist),
            metadata={},
        )
        
        return value_type
    
    def get_priority(self) -> int:
        """Get priority of this enhancer."""
        return 40  # High priority, run after constraint-based
