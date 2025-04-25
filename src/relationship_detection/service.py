"""
Service for relationship detection operations.
"""
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from src.format_detection.models import SchemaDetails
from src.format_detection.type_inference.service import TypeInferenceService
from src.relationship_detection.models import (
    RelationshipConfidence,
    SchemaRelationship,
    SchemaRelationshipStore,
)
from src.relationship_detection.strategies.base import RelationshipStrategy


logger = logging.getLogger(__name__)


class RelationshipDetectionService:
    """Service for relationship detection operations."""
    
    def __init__(self):
        """Initialize the relationship detection service."""
        self.strategies: List[RelationshipStrategy] = []
        self.type_inference_service = TypeInferenceService()
        self._register_strategies()
        logger.info("Initialized relationship detection service with %d strategies", len(self.strategies))
    
    def _register_strategies(self):
        """Register built-in relationship detection strategies."""
        # Lazily import strategies to avoid circular import issues
        from src.relationship_detection.strategies.foreign_key import ForeignKeyRelationshipStrategy
        from src.relationship_detection.strategies.name_based import NameBasedRelationshipStrategy
        from src.relationship_detection.strategies.structural import StructuralSimilarityStrategy
        
        # Register strategies in order of priority
        self.register_strategy(ForeignKeyRelationshipStrategy())
        self.register_strategy(NameBasedRelationshipStrategy())
        self.register_strategy(StructuralSimilarityStrategy())
        
        logger.info("Registered %d relationship detection strategies", len(self.strategies))
    
    def register_strategy(self, strategy: RelationshipStrategy):
        """
        Register a relationship detection strategy.
        
        Args:
            strategy: Strategy instance.
        """
        self.strategies.append(strategy)
        # Sort strategies by priority (ascending)
        self.strategies.sort(key=lambda s: s.get_priority())
        logger.debug("Registered strategy: %s (priority: %d)", 
                    strategy.get_id(), strategy.get_priority())
    
    async def detect_relationships(
        self, 
        schemas: List[SchemaDetails], 
        options: Optional[Dict[str, Any]] = None
    ) -> SchemaRelationshipStore:
        """
        Detect relationships between schemas.
        
        Args:
            schemas: List of schema details to analyze.
            options: Optional detection options.
            
        Returns:
            SchemaRelationshipStore: Detected relationships and metadata.
        """
        logger.info("Detecting relationships between %d schemas", len(schemas))
        
        if not schemas:
            logger.warning("No schemas provided for relationship detection")
            return SchemaRelationshipStore(
                relationships=[],
                schema_coverage={},
                confidence_summary={},
                metadata={"status": "no_schemas"}
            )
        
        # Apply options with defaults
        options = options or {}
        confidence_threshold = options.get("confidence_threshold", 0.5)
        max_relationships = options.get("max_relationships", 1000)
        
        # Enhance schemas with type inference if needed
        enhanced_schemas = schemas
        if options.get("enhance_types", True):
            enhanced_schemas = [
                self.type_inference_service.enhance_schema(schema) 
                for schema in schemas
            ]
            logger.debug("Enhanced schema types for relationship detection")
        
        # Collect all relationships from all strategies
        all_relationships: List[SchemaRelationship] = []
        
        for strategy in self.strategies:
            try:
                # Filter and preprocess schemas for this strategy
                filtered_schemas = strategy.filter_schemas(enhanced_schemas, options)
                preprocessed_schemas = strategy.preprocess_schemas(filtered_schemas, options)
                
                # Detect relationships
                logger.debug("Applying strategy: %s to %d schemas", 
                           strategy.get_id(), len(preprocessed_schemas))
                relationships = strategy.detect(preprocessed_schemas, options)
                
                # Postprocess relationships
                relationships = strategy.postprocess_relationships(
                    relationships, enhanced_schemas, options)
                
                logger.debug("Strategy %s detected %d relationships", 
                           strategy.get_id(), len(relationships))
                
                all_relationships.extend(relationships)
                
            except Exception as e:
                logger.error("Error in relationship detection strategy %s: %s", 
                            strategy.get_id(), str(e), exc_info=True)
        
        # Use utility function to consolidate relationships
        from src.relationship_detection.utils.confidence import consolidate_relationships
        consolidated = consolidate_relationships(all_relationships, confidence_threshold)
        
        # Limit number of relationships if needed
        if len(consolidated) > max_relationships:
            logger.warning("Limiting relationships to %d (from %d)", 
                         max_relationships, len(consolidated))
            consolidated = consolidated[:max_relationships]
        
        # Use utility functions to create schema coverage and calculate statistics
        from src.relationship_detection.utils.consolidation import (
            create_schema_coverage_map,
            calculate_coverage_statistics,
        )
        
        schema_coverage = create_schema_coverage_map(consolidated)
        
        # Calculate confidence summary
        confidence_summary = {
            "mean": sum([r.confidence.score for r in consolidated]) / len(consolidated) if consolidated else 0.0,
            "min": min([r.confidence.score for r in consolidated]) if consolidated else 0.0,
            "max": max([r.confidence.score for r in consolidated]) if consolidated else 0.0,
        }
        
        # Add by_type breakdown
        by_type = {}
        for rel in consolidated:
            rel_type = rel.relationship_type.value
            if rel_type not in by_type:
                by_type[rel_type] = []
            by_type[rel_type].append(rel.confidence.score)
        
        confidence_summary["by_type"] = {
            rel_type: sum(scores) / len(scores)
            for rel_type, scores in by_type.items()
        }
        
        # Create metadata
        metadata = {
            "total_schemas_analyzed": len(schemas),
            "total_relationships_detected": len(all_relationships),
            "total_relationships_after_consolidation": len(consolidated),
            "strategies_applied": [s.get_id() for s in self.strategies],
            "options": options,
        }
        
        # Create relationship store
        relationship_store = SchemaRelationshipStore(
            relationships=consolidated,
            schema_coverage=schema_coverage,
            confidence_summary=confidence_summary,
            metadata=metadata,
        )
        
        logger.info("Detected %d relationships (after consolidation) between %d schemas", 
                   len(consolidated), len(schemas))
        return relationship_store
    
    def _consolidate_relationships(
        self,
        relationships: List[SchemaRelationship],
        confidence_threshold: float = 0.5
    ) -> List[SchemaRelationship]:
        """
        Consolidate and filter relationships.
        
        Args:
            relationships: List of detected relationships.
            confidence_threshold: Minimum confidence threshold.
            
        Returns:
            List[SchemaRelationship]: Consolidated relationships.
        """
        # Filter by confidence
        filtered = [r for r in relationships if r.confidence.score >= confidence_threshold]
        
        # Group by source and target schema
        grouped: Dict[Tuple[str, str], List[SchemaRelationship]] = {}
        for rel in filtered:
            key = (rel.source_schema, rel.target_schema)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(rel)
        
        # Consolidate each group
        consolidated: List[SchemaRelationship] = []
        for (source, target), group in grouped.items():
            if len(group) == 1:
                # Only one relationship, keep as is
                consolidated.append(group[0])
            else:
                # Multiple relationships, consolidate
                consolidated.append(self._merge_relationships(group))
        
        # Sort by confidence score (descending)
        consolidated.sort(key=lambda r: r.confidence.score, reverse=True)
        
        return consolidated
    
    def _merge_relationships(self, relationships: List[SchemaRelationship]) -> SchemaRelationship:
        """
        Merge multiple relationships between the same schemas.
        
        Args:
            relationships: List of relationships to merge.
            
        Returns:
            SchemaRelationship: Merged relationship.
        """
        # Select the highest confidence relationship as base
        base = max(relationships, key=lambda r: r.confidence.score)
        
        # Collect all confidence factors
        all_factors: Dict[str, List[float]] = {}
        for rel in relationships:
            for factor, value in rel.confidence.factors.items():
                if factor not in all_factors:
                    all_factors[factor] = []
                all_factors[factor].append(value)
        
        # Average the factors
        merged_factors = {factor: sum(values) / len(values) 
                         for factor, values in all_factors.items()}
        
        # Add a "multiple_signals" boost if multiple strategies detected this relationship
        strategy_set = {rel.confidence.detection_method for rel in relationships}
        if len(strategy_set) > 1:
            merged_factors["multiple_signals"] = 0.1 * min(len(strategy_set), 3)
        
        # Calculate merged confidence score
        base_score = sum(merged_factors.values())
        merged_score = max(0.1, min(1.0, base_score))
        
        # Create merged confidence
        merged_confidence = RelationshipConfidence(
            score=merged_score,
            factors=merged_factors,
            rationale=f"Merged from {len(relationships)} relationship detections",
            detection_method=", ".join(sorted(strategy_set)),
        )
        
        # Create merged relationship
        return SchemaRelationship(
            source_schema=base.source_schema,
            target_schema=base.target_schema,
            source_fields=base.source_fields,
            target_fields=base.target_fields,
            relationship_type=base.relationship_type,
            confidence=merged_confidence,
            bidirectional=base.bidirectional,
            metadata={
                "merged_from": len(relationships),
                "original_methods": list(strategy_set),
            },
        )
    
    def _create_schema_coverage(self, relationships: List[SchemaRelationship]) -> Dict[str, List[str]]:
        """
        Create schema coverage mapping.
        
        Args:
            relationships: List of relationships.
            
        Returns:
            Dict[str, List[str]]: Mapping from schema ID to related schemas.
        """
        coverage: Dict[str, Set[str]] = {}
        
        for rel in relationships:
            source = rel.source_schema
            target = rel.target_schema
            
            if source not in coverage:
                coverage[source] = set()
            coverage[source].add(target)
            
            # Add bidirectional reference if needed
            if rel.bidirectional:
                if target not in coverage:
                    coverage[target] = set()
                coverage[target].add(source)
        
        # Convert sets to sorted lists
        return {
            schema: sorted(list(related)) 
            for schema, related in coverage.items()
        }
    
    def _calculate_mean_confidence(self, relationships: List[SchemaRelationship]) -> float:
        """
        Calculate mean confidence score across all relationships.
        
        Args:
            relationships: List of relationships.
            
        Returns:
            float: Mean confidence score (0.0 if no relationships).
        """
        if not relationships:
            return 0.0
            
        total = sum(rel.confidence.score for rel in relationships)
        return total / len(relationships)
    
    def _calculate_confidence_by_type(self, relationships: List[SchemaRelationship]) -> Dict[str, float]:
        """
        Calculate mean confidence score by relationship type.
        
        Args:
            relationships: List of relationships.
            
        Returns:
            Dict[str, float]: Mean confidence by relationship type.
        """
        by_type: Dict[str, List[float]] = {}
        
        for rel in relationships:
            rel_type = rel.relationship_type.value
            if rel_type not in by_type:
                by_type[rel_type] = []
            by_type[rel_type].append(rel.confidence.score)
        
        return {
            rel_type: sum(scores) / len(scores)
            for rel_type, scores in by_type.items()
        }
