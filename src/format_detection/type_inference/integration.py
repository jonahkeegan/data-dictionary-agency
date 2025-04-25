"""
Integration between type inference system and format detection service.
"""
import logging
from typing import Dict, Any, List, Optional

from src.format_detection.models import SchemaDetails, FormatType
from src.format_detection.type_inference.service import TypeInferenceService

logger = logging.getLogger(__name__)


class TypeInferenceIntegration:
    """
    Integration between format detection service and type inference system.
    
    This class provides methods to enhance schema information extracted by the
    format detection system using the type inference capabilities.
    """
    
    def __init__(self):
        """Initialize the type inference integration."""
        self.type_inference_service = TypeInferenceService()
        logger.info("Initialized type inference integration")
    
    def enhance_schema(self, schema: SchemaDetails, format_id: str) -> SchemaDetails:
        """
        Enhance schema with improved type information.
        
        Args:
            schema: Schema details from format detection.
            format_id: Format identifier.
            
        Returns:
            SchemaDetails: Enhanced schema details.
        """
        logger.info("Enhancing schema for format: %s", format_id)
        
        # Add format-specific context
        format_context = {
            'format_id': format_id,
            'format_specific': self._get_format_specific_context(format_id),
        }
        
        # Use type inference service to enhance schema
        enhanced_schema = self.type_inference_service.enhance_schema(schema)
        
        # Add format-specific metadata
        if enhanced_schema.metadata is None:
            enhanced_schema.metadata = {}
            
        enhanced_schema.metadata['format_id'] = format_id
        enhanced_schema.metadata['type_inference_applied'] = True
        
        logger.info("Enhanced schema with %d fields for format: %s", 
                   len(enhanced_schema.fields), format_id)
        
        return enhanced_schema
    
    def _get_format_specific_context(self, format_id: str) -> Dict[str, Any]:
        """
        Get format-specific context information for type inference.
        
        Args:
            format_id: Format identifier.
            
        Returns:
            Dict[str, Any]: Format-specific context.
        """
        # This can be extended with format-specific information
        # For example, certain formats might have known type patterns or conventions
        
        format_context = {}
        
        try:
            format_type = FormatType(format_id)
            
            # Add format-specific context based on format type
            if format_type == FormatType.JSON:
                format_context = {
                    'allows_mixed_types_in_arrays': True,
                    'typical_id_field': 'id',
                    'number_handling': 'native',
                }
            elif format_type == FormatType.CSV:
                format_context = {
                    'column_based': True,
                    'uniform_types': True,
                    'first_row_header': True,
                }
            elif format_type == FormatType.SQL:
                format_context = {
                    'strict_types': True,
                    'supports_constraints': True,
                    'primary_key_convention': 'id',
                }
            elif format_type == FormatType.PROTOBUF:
                format_context = {
                    'strict_types': True,
                    'supports_nested_types': True,
                    'supports_unions': False,
                    'common_conventions': {
                        'timestamp': 'google.protobuf.Timestamp',
                        'nullable': 'google.protobuf.StringValue',
                    }
                }
            elif format_type == FormatType.GRAPHQL:
                format_context = {
                    'supports_interfaces': True,
                    'supports_unions': True,
                    'supports_scalars': True,
                    'common_conventions': {
                        'id': 'ID',
                        'timestamp': 'DateTime',
                    }
                }
            # Add more format-specific contexts as needed
            
        except ValueError:
            logger.warning("Unknown format ID: %s", format_id)
        
        return format_context
