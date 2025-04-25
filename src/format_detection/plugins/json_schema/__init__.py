"""
JSON Schema format parser plugin.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Union

from src.format_detection.models import (
    DataType,
    FieldConstraint,
    FieldInfo,
    FormatType,
    SchemaDetails,
)

logger = logging.getLogger(__name__)

# JSON Schema type to normalized data type mapping
JSON_SCHEMA_TYPE_MAPPING = {
    "string": DataType.STRING,
    "integer": DataType.INTEGER,
    "number": DataType.FLOAT,
    "boolean": DataType.BOOLEAN,
    "array": DataType.ARRAY,
    "object": DataType.OBJECT,
    "null": DataType.NULL,
}

# JSON Schema format to data type mapping
JSON_SCHEMA_FORMAT_MAPPING = {
    "date": DataType.DATE,
    "date-time": DataType.DATETIME,
    "time": DataType.STRING,
    "email": DataType.STRING,
    "uri": DataType.STRING,
    "uuid": DataType.UUID,
    "binary": DataType.BINARY,
}


class JSONSchemaParser:
    """Parser for JSON Schema files."""

    def can_parse(self, filename: str, content: bytes) -> bool:
        """
        Check if the file content can be parsed as a JSON Schema.
        
        Args:
            filename: Name of the file
            content: File content
            
        Returns:
            bool: True if the content appears to be a JSON Schema, False otherwise
        """
        if not content:
            return False
            
        try:
            # Try to decode and parse the JSON content
            text = content.decode('utf-8', errors='strict')
            schema = json.loads(text)
            
            # Check for JSON Schema indicators
            indicators = [
                # JSON Schema keywords/properties
                "$schema" in schema,
                "type" in schema,
                "properties" in schema,
                "$ref" in schema,
                "definitions" in schema,
                "$id" in schema,
                "allOf" in schema,
                "anyOf" in schema,
                "oneOf" in schema,
                
                # JSON Schema specific values
                schema.get("$schema", "").startswith("http://json-schema.org/"),
                schema.get("$schema", "").startswith("https://json-schema.org/"),
            ]
            
            # If at least two indicators match, likely a JSON Schema
            if sum(bool(ind) for ind in indicators) >= 2:
                return True
                
            # Check filename patterns
            if filename.endswith('.schema.json') or filename.endswith('.json-schema'):
                return True
                
            return False
            
        except (UnicodeDecodeError, json.JSONDecodeError):
            # Not a valid JSON file
            return False

    def get_format_type(self) -> FormatType:
        """
        Get the format type handled by this parser.
        
        Returns:
            FormatType: The format type for JSON Schema
        """
        return FormatType.JSON_SCHEMA

    def parse_schema(self, filename: str, content: bytes) -> SchemaDetails:
        """
        Parse JSON Schema file and extract schema details.
        
        Args:
            filename: Name of the file
            content: File content
            
        Returns:
            SchemaDetails: Extracted schema details
        """
        logger.info(f"Parsing JSON Schema from file: {filename}")
        
        try:
            text = content.decode('utf-8', errors='strict')
            schema = json.loads(text)
            
            # Extract schema information
            fields = []
            primary_keys = []
            unique_constraints = []
            
            # Process schema properties
            schema_title = schema.get('title', 'Root')
            properties = schema.get('properties', {})
            required_fields = schema.get('required', [])
            
            for prop_name, prop_def in properties.items():
                # Extract field data
                field_type = prop_def.get('type')
                field_format = prop_def.get('format')
                description = prop_def.get('description')
                
                # Determine normalized data type
                if isinstance(field_type, list):
                    # Handle multiple types
                    data_type = self._get_primary_type(field_type, field_format)
                elif field_type:
                    # Single type
                    data_type = self._map_type(field_type, field_format)
                else:
                    # No type specified
                    data_type = DataType.UNKNOWN
                
                # Extract constraints
                constraints = self._extract_constraints(prop_name, prop_def, required_fields)
                
                # Check if field could be a primary key
                if self._is_potential_primary_key(prop_name, prop_def):
                    primary_keys.append(prop_name)
                
                # Check for uniqueness constraints
                if prop_def.get('uniqueItems') or 'uniqueItems' in prop_def:
                    if isinstance(prop_def.get('uniqueItems'), bool) and prop_def.get('uniqueItems'):
                        unique_constraints.append([prop_name])
                
                # Create field info
                field_info = FieldInfo(
                    name=prop_name,
                    path=prop_name,
                    data_type=data_type,
                    nullable=prop_name not in required_fields,
                    description=description,
                    constraints=constraints,
                    metadata={
                        "json_schema_type": field_type,
                        "json_schema_format": field_format,
                        "parent_schema": schema_title,
                    }
                )
                
                fields.append(field_info)
                
                # Handle nested properties for objects
                if data_type == DataType.OBJECT and 'properties' in prop_def:
                    nested_fields = self._process_nested_properties(
                        prop_name, 
                        prop_def.get('properties', {}),
                        prop_def.get('required', [])
                    )
                    fields.extend(nested_fields)
            
            # Create schema details
            return SchemaDetails(
                fields=fields,
                primary_keys=primary_keys,
                unique_constraints=unique_constraints,
                metadata={
                    "schema_type": "json_schema",
                    "source_file": filename,
                    "schema_title": schema.get('title'),
                    "schema_description": schema.get('description'),
                    "schema_version": schema.get('$schema'),
                }
            )
            
        except Exception as e:
            logger.error(f"Error parsing JSON Schema: {str(e)}")
            # Return an empty schema in case of error
            return SchemaDetails(
                fields=[],
                metadata={
                    "schema_type": "json_schema",
                    "source_file": filename,
                    "error": str(e)
                }
            )
    
    def _map_type(self, json_type: str, json_format: Optional[str] = None) -> DataType:
        """
        Map JSON Schema type and format to normalized data type.
        
        Args:
            json_type: JSON Schema type
            json_format: JSON Schema format (optional)
            
        Returns:
            DataType: Normalized data type
        """
        if json_format and json_format in JSON_SCHEMA_FORMAT_MAPPING:
            return JSON_SCHEMA_FORMAT_MAPPING[json_format]
        
        return JSON_SCHEMA_TYPE_MAPPING.get(json_type, DataType.UNKNOWN)
    
    def _get_primary_type(self, type_list: List[str], json_format: Optional[str] = None) -> DataType:
        """
        Get primary data type from a list of possible types.
        
        Args:
            type_list: List of JSON Schema types
            json_format: JSON Schema format (optional)
            
        Returns:
            DataType: Primary normalized data type
        """
        # Handle format first if present
        if json_format and json_format in JSON_SCHEMA_FORMAT_MAPPING:
            return JSON_SCHEMA_FORMAT_MAPPING[json_format]
        
        # If 'null' is one of multiple types, use the other type
        non_null_types = [t for t in type_list if t != 'null']
        if non_null_types:
            # Use the first non-null type
            return JSON_SCHEMA_TYPE_MAPPING.get(non_null_types[0], DataType.UNKNOWN)
        
        return DataType.NULL if 'null' in type_list else DataType.UNKNOWN
    
    def _extract_constraints(
        self, field_name: str, field_def: Dict[str, Any], required_fields: List[str]
    ) -> List[FieldConstraint]:
        """
        Extract constraints from JSON Schema field definition.
        
        Args:
            field_name: Field name
            field_def: Field definition
            required_fields: List of required field names
            
        Returns:
            List[FieldConstraint]: List of extracted field constraints
        """
        constraints = []
        
        # Required constraint
        if field_name in required_fields:
            constraints.append(
                FieldConstraint(
                    type="required",
                    value=True,
                    description="Field is required"
                )
            )
        
        # Minimum/maximum for numbers
        if 'minimum' in field_def:
            constraints.append(
                FieldConstraint(
                    type="minimum",
                    value=field_def['minimum'],
                    description=f"Minimum value: {field_def['minimum']}"
                )
            )
        
        if 'maximum' in field_def:
            constraints.append(
                FieldConstraint(
                    type="maximum",
                    value=field_def['maximum'],
                    description=f"Maximum value: {field_def['maximum']}"
                )
            )
        
        # String constraints
        if 'minLength' in field_def:
            constraints.append(
                FieldConstraint(
                    type="minLength",
                    value=field_def['minLength'],
                    description=f"Minimum length: {field_def['minLength']}"
                )
            )
        
        if 'maxLength' in field_def:
            constraints.append(
                FieldConstraint(
                    type="maxLength",
                    value=field_def['maxLength'],
                    description=f"Maximum length: {field_def['maxLength']}"
                )
            )
        
        if 'pattern' in field_def:
            constraints.append(
                FieldConstraint(
                    type="pattern",
                    value=field_def['pattern'],
                    description=f"Regex pattern: {field_def['pattern']}"
                )
            )
        
        # Array constraints
        if 'minItems' in field_def:
            constraints.append(
                FieldConstraint(
                    type="minItems",
                    value=field_def['minItems'],
                    description=f"Minimum items: {field_def['minItems']}"
                )
            )
        
        if 'maxItems' in field_def:
            constraints.append(
                FieldConstraint(
                    type="maxItems",
                    value=field_def['maxItems'],
                    description=f"Maximum items: {field_def['maxItems']}"
                )
            )
        
        # Enum constraints
        if 'enum' in field_def:
            constraints.append(
                FieldConstraint(
                    type="enum",
                    value=field_def['enum'],
                    description=f"Enumerated values: {field_def['enum']}"
                )
            )
        
        return constraints
    
    def _is_potential_primary_key(self, field_name: str, field_def: Dict[str, Any]) -> bool:
        """
        Determine if a field is a potential primary key.
        
        Args:
            field_name: Field name
            field_def: Field definition
            
        Returns:
            bool: True if the field could be a primary key
        """
        # Common primary key indicators
        indicators = [
            field_name.lower() == 'id',
            field_name.lower().endswith('id') and len(field_name) > 2,
            field_name.lower() == 'key',
            field_name.lower() == 'primarykey',
            field_def.get('format') == 'uuid',
            field_def.get('unique') is True,
            'readOnly' in field_def and field_def['readOnly'] is True,
        ]
        
        # Return True if any indicator matches
        return any(indicators)
    
    def _process_nested_properties(
        self, parent_path: str, properties: Dict[str, Any], required_fields: List[str]
    ) -> List[FieldInfo]:
        """
        Process nested properties from an object type.
        
        Args:
            parent_path: Path to parent object
            properties: Nested properties
            required_fields: List of required field names
            
        Returns:
            List[FieldInfo]: List of nested field information
        """
        nested_fields = []
        
        for prop_name, prop_def in properties.items():
            # Extract field data
            field_type = prop_def.get('type')
            field_format = prop_def.get('format')
            description = prop_def.get('description')
            
            # Determine full field path
            field_path = f"{parent_path}.{prop_name}"
            
            # Determine normalized data type
            if isinstance(field_type, list):
                # Handle multiple types
                data_type = self._get_primary_type(field_type, field_format)
            elif field_type:
                # Single type
                data_type = self._map_type(field_type, field_format)
            else:
                # No type specified
                data_type = DataType.UNKNOWN
            
            # Extract constraints
            constraints = self._extract_constraints(prop_name, prop_def, required_fields)
            
            # Create field info
            field_info = FieldInfo(
                name=prop_name,
                path=field_path,
                data_type=data_type,
                nullable=prop_name not in required_fields,
                description=description,
                constraints=constraints,
                metadata={
                    "json_schema_type": field_type,
                    "json_schema_format": field_format,
                    "parent_path": parent_path,
                }
            )
            
            nested_fields.append(field_info)
            
            # Further nesting for objects
            if data_type == DataType.OBJECT and 'properties' in prop_def:
                deeper_nested = self._process_nested_properties(
                    field_path,
                    prop_def.get('properties', {}),
                    prop_def.get('required', [])
                )
                nested_fields.extend(deeper_nested)
        
        return nested_fields


# Export the parser class
parser = JSONSchemaParser()

def register_plugin():
    """Register the JSON Schema parser plugin."""
    return {
        "format_id": "json_schema",
        "parser": parser,
        "priority": 55,  # Mid-level priority, slightly higher than GraphQL
        "description": "JSON Schema parser"
    }
