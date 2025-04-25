"""
Base strategy class for relationship detection.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.format_detection.models import SchemaDetails
from src.relationship_detection.models import SchemaRelationship


logger = logging.getLogger(__name__)


class RelationshipStrategy(ABC):
    """Abstract base class for all relationship detection strategies."""
    
    @abstractmethod
    def detect(self, schemas: List[SchemaDetails], options: Optional[Dict[str, Any]] = None) -> List[SchemaRelationship]:
        """
        Detect relationships between schemas.
        
        Args:
            schemas: List of schema details to analyze.
            options: Optional detection options.
            
        Returns:
            List[SchemaRelationship]: Detected relationships.
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """
        Get priority of this strategy.
        
        Returns:
            int: Priority (higher values will be executed later).
        """
        pass
    
    def get_id(self) -> str:
        """
        Get unique identifier for this strategy.
        
        Returns:
            str: Strategy identifier.
        """
        return self.__class__.__name__
    
    def get_description(self) -> str:
        """
        Get description of this strategy.
        
        Returns:
            str: Strategy description.
        """
        return self.__class__.__doc__ or "No description available"
    
    def filter_schemas(self, schemas: List[SchemaDetails], options: Optional[Dict[str, Any]] = None) -> List[SchemaDetails]:
        """
        Filter schemas before detection.
        
        Args:
            schemas: List of schema details to filter.
            options: Optional filtering options.
            
        Returns:
            List[SchemaDetails]: Filtered schemas.
        """
        # Default implementation: no filtering
        return schemas
    
    def preprocess_schemas(self, schemas: List[SchemaDetails], options: Optional[Dict[str, Any]] = None) -> List[SchemaDetails]:
        """
        Preprocess schemas before detection.
        
        Args:
            schemas: List of schema details to preprocess.
            options: Optional preprocessing options.
            
        Returns:
            List[SchemaDetails]: Preprocessed schemas.
        """
        # Default implementation: no preprocessing
        return schemas
    
    def postprocess_relationships(self, relationships: List[SchemaRelationship], 
                                 schemas: List[SchemaDetails],
                                 options: Optional[Dict[str, Any]] = None) -> List[SchemaRelationship]:
        """
        Postprocess detected relationships.
        
        Args:
            relationships: List of detected relationships.
            schemas: List of schema details.
            options: Optional postprocessing options.
            
        Returns:
            List[SchemaRelationship]: Postprocessed relationships.
        """
        # Default implementation: no postprocessing
        return relationships
