"""
Service for enhanced type inference operations.
"""
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from src.format_detection.models import DataType, FieldInfo, SchemaDetails
from src.format_detection.type_inference.models import (
    EnhancedTypeInfo,
    NormalizedType,
    TypeAlternative,
    TypeConfidence,
    TypeConstraintEnhanced,
    TypePattern,
)


logger = logging.getLogger(__name__)


class TypeEnhancer(ABC):
    """Abstract base class for type enhancers."""
    
    @abstractmethod
    def enhance_type(self, field_info: FieldInfo, context: Dict[str, Any]) -> EnhancedTypeInfo:
        """
        Enhance type information for a field.
        
        Args:
            field_info: Field information.
            context: Additional context for type inference.
            
        Returns:
            EnhancedTypeInfo: Enhanced type information.
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """
        Get priority of this enhancer.
        
        Returns:
            int: Priority (higher values will be executed later).
        """
        pass


class TypeInferenceService:
    """Service for enhanced type inference operations."""
    
    def __init__(self):
        """Initialize the type inference service."""
        self.enhancers: List[TypeEnhancer] = []
        self._register_enhancers()
        logger.info("Initialized type inference service with %d enhancers", len(self.enhancers))
    
    def _register_enhancers(self):
        """Register built-in type enhancers."""
        from src.format_detection.type_inference.enhancers import (
            NameBasedEnhancer,
            PatternBasedEnhancer,
            ConstraintBasedEnhancer,
            ComplexStructureEnhancer,
        )
        
        # Register enhancers in order of increasing priority
        # (they will be sorted by priority later)
        self.register_enhancer(NameBasedEnhancer())
        self.register_enhancer(PatternBasedEnhancer())
        self.register_enhancer(ConstraintBasedEnhancer())
        self.register_enhancer(ComplexStructureEnhancer())
        
        logger.info("Registered %d built-in type enhancers", len(self.enhancers))
    
    def register_enhancer(self, enhancer: TypeEnhancer):
        """
        Register a type enhancer.
        
        Args:
            enhancer: Type enhancer instance.
        """
        self.enhancers.append(enhancer)
        # Sort enhancers by priority (ascending)
        self.enhancers.sort(key=lambda e: e.get_priority())
        logger.debug("Registered enhancer: %s (priority: %d)", 
                    enhancer.__class__.__name__, enhancer.get_priority())
    
    def enhance_schema(self, schema: SchemaDetails) -> SchemaDetails:
        """
        Enhance type information in a schema.
        
        Args:
            schema: Schema details.
            
        Returns:
            SchemaDetails: Enhanced schema details.
        """
        logger.debug("Enhancing schema with %d fields", len(schema.fields))
        
        # Create context for schema-wide inference
        schema_context = {
            'field_names': [field.name for field in schema.fields],
            'primary_keys': schema.primary_keys,
            'foreign_keys': schema.foreign_keys,
            'unique_constraints': schema.unique_constraints,
        }
        
        # Enhance each field
        enhanced_fields = []
        type_confidence = {}
        
        for field in schema.fields:
            # Create field-specific context
            field_context = {
                **schema_context,
                'field_path': field.path,
                'nullable': field.nullable,
                'sample_values': field.sample_values,
                'statistics': field.statistics or {},
            }
            
            # Enhance type information
            enhanced_type = self.infer_field_type(field, field_context)
            
            # Store enhanced type information
            enhanced_field = field.copy()
            enhanced_field.metadata = {
                **(enhanced_field.metadata or {}),
                'enhanced_type': enhanced_type.dict(),
            }
            
            enhanced_fields.append(enhanced_field)
            type_confidence[field.path] = enhanced_type.confidence.score
        
        # Create enhanced schema
        enhanced_schema = schema.copy()
        enhanced_schema.fields = enhanced_fields
        enhanced_schema.metadata = {
            **(enhanced_schema.metadata or {}),
            'type_confidence': type_confidence,
            'type_inference_version': '1.0.0',
        }
        
        return enhanced_schema
    
    def infer_field_type(self, field: FieldInfo, context: Dict[str, Any]) -> EnhancedTypeInfo:
        """
        Infer enhanced type information for a field.
        
        Args:
            field: Field information.
            context: Additional context for type inference.
            
        Returns:
            EnhancedTypeInfo: Enhanced type information.
        """
        logger.debug("Inferring type for field: %s", field.path)
        
        # Apply each enhancer in order of priority
        current_type = self._create_base_type_info(field)
        
        for enhancer in self.enhancers:
            try:
                enhanced_type = enhancer.enhance_type(field, {
                    **context,
                    'current_type': current_type,
                })
                current_type = enhanced_type
                logger.debug("Applied enhancer %s to field %s", 
                           enhancer.__class__.__name__, field.path)
            except Exception as e:
                logger.warning("Enhancer %s failed for field %s: %s", 
                              enhancer.__class__.__name__, field.path, str(e))
        
        # Final confidence adjustment based on all available information
        current_type.confidence = self._finalize_confidence_score(current_type, field, context)
        
        return current_type
    
    def _create_base_type_info(self, field: FieldInfo) -> EnhancedTypeInfo:
        """
        Create baseline type information from field data.
        
        Args:
            field: Field information.
            
        Returns:
            EnhancedTypeInfo: Base type information.
        """
        # Start with the data type declared in the field
        primary_type = field.data_type
        
        # Create initial confidence based on the presence of explicit type information
        confidence = TypeConfidence(
            score=0.7,  # Default confidence for explicitly declared types
            factors={"explicit_declaration": 0.7},
            rationale="Based on explicit type declaration",
            detection_method="parser_declared",
        )
        
        return EnhancedTypeInfo(
            primary_type=primary_type,
            secondary_types=[],
            format_specific_type=None,
            constraints=field.constraints,
            patterns=[],
            confidence=confidence,
            possible_alternatives=[],
            is_nullable=field.nullable,
            metadata={},
        )
    
    def _finalize_confidence_score(
        self, type_info: EnhancedTypeInfo, field: FieldInfo, context: Dict[str, Any]
    ) -> TypeConfidence:
        """
        Finalize confidence score for a type inference.
        
        Args:
            type_info: Current type information.
            field: Field information.
            context: Inference context.
            
        Returns:
            TypeConfidence: Final confidence information.
        """
        confidence = type_info.confidence
        
        # Adjust based on number of supporting factors
        num_factors = len(confidence.factors)
        if num_factors >= 3:
            confidence.factors["multiple_indicators"] = 0.1
        
        # Adjust based on pattern detection
        if type_info.patterns:
            confidence.factors["pattern_match"] = 0.1
        
        # Adjust for conflicting signals
        alternatives_count = len(type_info.possible_alternatives)
        if alternatives_count > 0:
            confidence.factors["ambiguity_penalty"] = -0.1 * min(alternatives_count, 3)
        
        # Recalculate final score
        confidence.score = 0.5  # Base score
        for factor, value in confidence.factors.items():
            confidence.score += value
        
        # Ensure score is within bounds
        confidence.score = max(0.1, min(1.0, confidence.score))
        
        return confidence
    
    def normalize_type(self, type_info: EnhancedTypeInfo, 
                      target_format: Optional[str] = None) -> NormalizedType:
        """
        Normalize type information to a format-neutral representation.
        
        Args:
            type_info: Enhanced type information.
            target_format: Optional target format for specific conversion.
            
        Returns:
            NormalizedType: Normalized type representation.
        """
        # Simple implementation - would be extended for complex formats
        normalized = NormalizedType(
            base_type=type_info.primary_type,
            format=target_format or "generic",
            format_specific_type=type_info.format_specific_type,
            constraints=type_info.constraints,
            is_nullable=type_info.is_nullable,
            metadata={
                "patterns": [p.value for p in type_info.patterns],
                "confidence": type_info.confidence.score,
            },
        )
        
        # Handle complex types recursively
        if type_info.primary_type == DataType.ARRAY and type_info.item_type:
            item_normalized = self.normalize_type(type_info.item_type, target_format)
            normalized.parameters.append(item_normalized)
        
        elif type_info.primary_type == DataType.OBJECT and type_info.properties:
            for name, prop_type in type_info.properties.items():
                normalized.properties[name] = self.normalize_type(prop_type, target_format)
        
        return normalized

    def denormalize_type(self, normalized: NormalizedType, 
                        target_format: str) -> EnhancedTypeInfo:
        """
        Convert a normalized type to a format-specific enhanced type.
        
        Args:
            normalized: Normalized type information.
            target_format: Target format for conversion.
            
        Returns:
            EnhancedTypeInfo: Format-specific enhanced type.
        """
        # This is a placeholder implementation
        # In a real implementation, would use format-specific handlers
        confidence = TypeConfidence(
            score=normalized.metadata.get("confidence", 0.7),
            factors={"normalized_conversion": 0.7},
            rationale=f"Converted from normalized type to {target_format}",
            detection_method="denormalization",
        )
        
        patterns = []
        for pattern_str in normalized.metadata.get("patterns", []):
            try:
                patterns.append(TypePattern(pattern_str))
            except ValueError:
                logger.warning("Unknown pattern in normalized type: %s", pattern_str)
        
        enhanced = EnhancedTypeInfo(
            primary_type=normalized.base_type,
            secondary_types=[],
            format_specific_type=None,  # Would be populated based on target format
            constraints=normalized.constraints,
            patterns=patterns,
            confidence=confidence,
            possible_alternatives=[],
            is_nullable=normalized.is_nullable,
            metadata=normalized.metadata,
        )
        
        # Handle complex types recursively
        if normalized.base_type == DataType.ARRAY and normalized.parameters:
            enhanced.item_type = self.denormalize_type(normalized.parameters[0], target_format)
            
        elif normalized.base_type == DataType.OBJECT and normalized.properties:
            enhanced.properties = {}
            for name, prop_type in normalized.properties.items():
                enhanced.properties[name] = self.denormalize_type(prop_type, target_format)
                
        return enhanced
