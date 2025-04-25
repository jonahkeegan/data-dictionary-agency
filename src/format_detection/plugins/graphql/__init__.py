"""
GraphQL schema format parser plugin.
"""
import logging
import re
from typing import Any, Dict, List, Optional

from src.format_detection.models import (
    DataType,
    FieldConstraint,
    FieldInfo,
    FormatType,
    SchemaDetails,
)

logger = logging.getLogger(__name__)

# Regular expressions for GraphQL schema parsing
TYPE_DEFINITION_REGEX = r'type\s+(\w+)(?:\s+implements\s+(?:\w+\s*&?\s*)*)\s*\{([^}]*)\}'
INTERFACE_DEFINITION_REGEX = r'interface\s+(\w+)(?:\s+implements\s+(?:\w+\s*&?\s*)*)\s*\{([^}]*)\}'
INPUT_DEFINITION_REGEX = r'input\s+(\w+)\s*\{([^}]*)\}'
ENUM_DEFINITION_REGEX = r'enum\s+(\w+)\s*\{([^}]*)\}'
SCALAR_DEFINITION_REGEX = r'scalar\s+(\w+)'
UNION_DEFINITION_REGEX = r'union\s+(\w+)\s*=\s*([^{]+)'
FIELD_REGEX = r'\s*(\w+)(?:\([^)]*\))?\s*:\s*(\w+)(?:!)?(?:\s*\[[^\]]*\])?'
COMMENT_REGEX = r'#([^\n]*)'

# GraphQL to normalized data type mapping
GRAPHQL_TYPE_MAPPING = {
    'String': DataType.STRING,
    'Int': DataType.INTEGER,
    'Float': DataType.FLOAT,
    'Boolean': DataType.BOOLEAN,
    'ID': DataType.UUID,
    # Add additional GraphQL types as needed
}


class GraphQLParser:
    """Parser for GraphQL schema files."""

    def can_parse(self, filename: str, content: bytes) -> bool:
        """
        Check if the file content can be parsed as a GraphQL schema.
        
        Args:
            filename: Name of the file
            content: File content
            
        Returns:
            bool: True if the content appears to be a GraphQL schema, False otherwise
        """
        if not content:
            return False
            
        try:
            text = content.decode('utf-8', errors='strict')
            
            # Look for common GraphQL schema indicators
            indicators = [
                r'type\s+\w+',
                r'input\s+\w+',
                r'interface\s+\w+',
                r'enum\s+\w+',
                r'scalar\s+\w+',
                r'union\s+\w+',
                r'schema\s*\{',
                r'directive\s+@\w+'
            ]
            
            for indicator in indicators:
                if re.search(indicator, text):
                    return True
                    
            # Check if filename has common GraphQL extensions
            if filename.endswith('.graphql') or filename.endswith('.gql'):
                return True
                
            return False
            
        except UnicodeDecodeError:
            # Not a text file, so not a GraphQL schema
            return False

    def get_format_type(self) -> FormatType:
        """
        Get the format type handled by this parser.
        
        Returns:
            FormatType: The format type for GraphQL schemas
        """
        return FormatType.GRAPHQL

    def parse_schema(self, filename: str, content: bytes) -> SchemaDetails:
        """
        Parse GraphQL schema file and extract schema details.
        
        Args:
            filename: Name of the file
            content: File content
            
        Returns:
            SchemaDetails: Extracted schema details
        """
        logger.info(f"Parsing GraphQL schema from file: {filename}")
        
        try:
            text = content.decode('utf-8', errors='strict')
            
            # Extract GraphQL schema definitions
            fields = []
            primary_keys = []
            
            # Extract type definitions
            type_matches = re.finditer(TYPE_DEFINITION_REGEX, text)
            for match in type_matches:
                type_name = match.group(1)
                type_fields_str = match.group(2)
                
                # Parse fields in the type
                field_matches = re.finditer(FIELD_REGEX, type_fields_str)
                for field_match in field_matches:
                    field_name = field_match.group(1)
                    field_type = field_match.group(2)
                    
                    # Extract comments for description
                    field_description = None
                    comment_line = text[:field_match.start()].rfind('#')
                    if comment_line != -1:
                        line_start = text[:comment_line].rfind('\n') + 1
                        comment_text = text[line_start:comment_line].strip()
                        if comment_text.startswith('#'):
                            field_description = comment_text[1:].strip()
                    
                    # Check if field is required
                    nullable = '!' not in field_type
                    field_type_clean = field_type.replace('!', '')
                    
                    # Convert GraphQL type to normalized type
                    data_type = GRAPHQL_TYPE_MAPPING.get(field_type_clean, DataType.STRING)
                    
                    # Create constraints based on type
                    constraints = []
                    if not nullable:
                        constraints.append(
                            FieldConstraint(
                                type="required",
                                value=True,
                                description="Field is required (non-nullable)"
                            )
                        )
                    
                    # Handle ID field as potential primary key
                    if field_type_clean == 'ID':
                        primary_keys.append(field_name)
                        data_type = DataType.UUID
                    
                    # Create field info
                    field_info = FieldInfo(
                        name=field_name,
                        path=f"{type_name}.{field_name}",
                        data_type=data_type,
                        nullable=nullable,
                        description=field_description,
                        constraints=constraints,
                        metadata={
                            "graphql_type": field_type,
                            "parent_type": type_name,
                            "graphql_schema_type": "type"
                        }
                    )
                    
                    fields.append(field_info)
            
            # Also parse interfaces, enums, and other GraphQL schema elements
            # similar to type parsing above (simplified for brevity)
            
            return SchemaDetails(
                fields=fields,
                primary_keys=primary_keys,
                metadata={
                    "schema_type": "graphql",
                    "source_file": filename,
                }
            )
            
        except Exception as e:
            logger.error(f"Error parsing GraphQL schema: {str(e)}")
            # Return an empty schema in case of error
            return SchemaDetails(
                fields=[],
                metadata={
                    "schema_type": "graphql",
                    "source_file": filename,
                    "error": str(e)
                }
            )

# Export the parser class
parser = GraphQLParser()

def register_plugin():
    """Register the GraphQL schema parser plugin."""
    return {
        "format_id": "graphql",
        "parser": parser,
        "priority": 50,  # Mid-level priority
        "description": "GraphQL schema parser"
    }
