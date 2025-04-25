"""
Avro schema format parser plugin.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from src.format_detection.models import (
    DataType,
    FieldConstraint,
    FieldInfo,
    FormatType,
    SchemaDetails,
)

logger = logging.getLogger(__name__)

# Mapping of Avro types to normalized data types
AVRO_TYPE_MAPPING = {
    "null": DataType.NULL,
    "boolean": DataType.BOOLEAN,
    "int": DataType.INTEGER,
    "long": DataType.INTEGER,
    "float": DataType.FLOAT,
    "double": DataType.FLOAT,
    "bytes": DataType.BINARY,
    "string": DataType.STRING,
    "record": DataType.OBJECT,
    "enum": DataType.ENUM,
    "array": DataType.ARRAY,
    "map": DataType.OBJECT,
    "fixed": DataType.BINARY,
}


class AvroParser:
    """Parser for Avro schema files."""
    
    def extract_sample_data(self, filename: str, content: bytes, max_records: int = 10) -> List[Dict[str, Any]]:
        """
        Extract sample data from Avro schema content.
        
        Note: Avro schema doesn't contain sample data, so this method returns
        sample record structures based on the schema.
        
        Args:
            filename: Name of the file
            content: File content
            max_records: Maximum number of records to extract
            
        Returns:
            List[Dict[str, Any]]: Sample record structures
        """
        try:
            # Parse Avro schema JSON
            text = content.decode('utf-8', errors='strict')
            avro_schema = json.loads(text)
            
            # Create a sample record based on the schema structure
            sample_records = []
            
            # Generate a single sample record
            sample_record = {
                "schema_type": "Avro schema",
                "schema_name": avro_schema.get("name", "Unknown"),
                "namespace": avro_schema.get("namespace"),
                "fields": [],
            }
            
            # Extract fields for sample record
            if avro_schema.get("type") == "record" and "fields" in avro_schema:
                for field in avro_schema["fields"]:
                    field_info = {
                        "name": field.get("name"),
                        "type": self._format_avro_type(field.get("type")),
                        "doc": field.get("doc"),
                    }
                    
                    # Add default value if present
                    if "default" in field:
                        field_info["default"] = field["default"]
                    
                    sample_record["fields"].append(field_info)
            
            sample_records.append(sample_record)
            
            return sample_records
            
        except Exception as e:
            logger.error(f"Error extracting sample data: {str(e)}")
            return [{"error": str(e)}]

    def can_parse(self, filename: str, content: bytes) -> bool:
        """
        Check if the file content can be parsed as an Avro schema.
        
        Args:
            filename: Name of the file
            content: File content
            
        Returns:
            bool: True if the content appears to be an Avro schema, False otherwise
        """
        if not content:
            return False
            
        try:
            # Try to decode the content as UTF-8
            text = content.decode('utf-8', errors='strict')
            
            # Check for common file extensions
            if filename and filename.lower().endswith(('.avsc', '.avro.json')):
                return True
            
            # Try to parse as JSON
            try:
                data = json.loads(text)
                
                # Look for common Avro schema indicators
                indicators = [
                    # Type indicators
                    '"type"' in text and '"record"' in text,
                    '"type"' in text and '"fields"' in text,
                    
                    # Namespace indicators
                    '"namespace"' in text,
                    
                    # Field structures
                    '"fields"' in text and '[' in text and ']' in text,
                    
                    # Type pattern matches
                    bool(re.search(r'"type"\s*:\s*"record"', text)),
                    bool(re.search(r'"type"\s*:\s*(\[|\{|\")(?:null|boolean|int|long|float|double|bytes|string|record|enum|array|map|fixed)', text)),
                    
                    # Check actual JSON structure if parsing succeeded
                    isinstance(data, dict) and "type" in data and data["type"] == "record" and "fields" in data,
                    isinstance(data, dict) and "type" in data and isinstance(data["type"], list) and "null" in data["type"]
                ]
                
                # If at least two indicators match, likely an Avro schema
                return sum(bool(ind) for ind in indicators) >= 2
                
            except json.JSONDecodeError:
                # Not valid JSON
                return False
                
        except UnicodeDecodeError:
            # Not a text file
            return False
            
        return False

    def get_format_type(self) -> FormatType:
        """
        Get the format type handled by this parser.
        
        Returns:
            FormatType: The format type for Avro schemas
        """
        return FormatType.AVRO

    def parse_schema(self, filename: str, content: bytes) -> SchemaDetails:
        """
        Parse Avro schema file and extract schema details.
        
        Args:
            filename: Name of the file
            content: File content
            
        Returns:
            SchemaDetails: Extracted schema details
        """
        logger.info(f"Parsing Avro schema from file: {filename}")
        
        try:
            # Parse Avro schema JSON
            text = content.decode('utf-8', errors='strict')
            avro_schema = json.loads(text)
            
            # Extract schema information
            fields = []
            primary_keys = []
            
            # Get schema metadata
            metadata = {
                "schema_type": "avro",
                "source_file": filename,
                "namespace": avro_schema.get("namespace"),
                "name": avro_schema.get("name"),
                "doc": avro_schema.get("doc"),
                "aliases": avro_schema.get("aliases"),
            }
            
            # Process schema and extract fields
            self._process_schema(avro_schema, fields, primary_keys)
            
            return SchemaDetails(
                fields=fields,
                primary_keys=primary_keys,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing Avro schema: {str(e)}")
            # Return an empty schema in case of error
            return SchemaDetails(
                fields=[],
                metadata={
                    "schema_type": "avro",
                    "source_file": filename,
                    "error": str(e)
                }
            )
    
    def _process_schema(self, schema: Any, fields: List[FieldInfo], primary_keys: List[str], parent_path: str = "") -> None:
        """
        Process Avro schema and extract field information.
        
        Args:
            schema: Avro schema object
            fields: List to append fields to
            primary_keys: List to append primary keys to
            parent_path: Path to parent element
        """
        # Handle top-level record
        if isinstance(schema, dict) and schema.get("type") == "record":
            record_name = schema.get("name", "record")
            record_doc = schema.get("doc", "")
            record_fields = schema.get("fields", [])
            
            # Process each field in the record
            for field in record_fields:
                field_name = field.get("name")
                field_path = f"{parent_path}.{field_name}" if parent_path else field_name
                field_type = field.get("type")
                field_doc = field.get("doc", "")
                
                # Extract constraints
                constraints = self._extract_constraints(field)
                
                # Determine if field is nullable
                nullable = self._is_nullable(field_type)
                
                # Extract data type and handle complex types
                data_type, type_info = self._extract_avro_type(field_type)
                
                # Check if field could be a primary key
                if self._is_potential_primary_key(field_name):
                    primary_keys.append(field_name)
                
                # Create field info
                field_info = FieldInfo(
                    name=field_name,
                    path=field_path,
                    data_type=data_type,
                    nullable=nullable,
                    description=field_doc,
                    constraints=constraints,
                    metadata={
                        "avro_type": field_type if isinstance(field_type, str) else self._format_avro_type(field_type),
                        "aliases": field.get("aliases"),
                        "parent_name": record_name,
                    }
                )
                
                fields.append(field_info)
                
                # Process nested types recursively
                self._process_nested_types(field_type, fields, primary_keys, field_path)
    
    def _process_nested_types(self, field_type: Any, fields: List[FieldInfo], primary_keys: List[str], parent_path: str) -> None:
        """
        Process nested types in Avro schema.
        
        Args:
            field_type: Avro field type
            fields: List to append fields to
            primary_keys: List to append primary keys to
            parent_path: Path to parent element
        """
        # Process record type
        if isinstance(field_type, dict) and field_type.get("type") == "record":
            self._process_schema(field_type, fields, primary_keys, parent_path)
        
        # Process array type
        elif isinstance(field_type, dict) and field_type.get("type") == "array":
            items_type = field_type.get("items")
            items_path = f"{parent_path}.items"
            
            # Process items if they're a record type
            if isinstance(items_type, dict) and items_type.get("type") == "record":
                self._process_schema(items_type, fields, primary_keys, items_path)
            
        # Process map type
        elif isinstance(field_type, dict) and field_type.get("type") == "map":
            values_type = field_type.get("values")
            values_path = f"{parent_path}.values"
            
            # Process values if they're a record type
            if isinstance(values_type, dict) and values_type.get("type") == "record":
                self._process_schema(values_type, fields, primary_keys, values_path)
        
        # Process union type
        elif isinstance(field_type, list):
            # Find the non-null type in the union
            for union_type in field_type:
                if union_type != "null" and isinstance(union_type, dict):
                    self._process_nested_types(union_type, fields, primary_keys, parent_path)
    
    def _extract_constraints(self, field: Dict[str, Any]) -> List[FieldConstraint]:
        """
        Extract constraints from Avro field definition.
        
        Args:
            field: Avro field definition
            
        Returns:
            List[FieldConstraint]: List of field constraints
        """
        constraints = []
        
        # Default value constraint
        if "default" in field:
            constraints.append(
                FieldConstraint(
                    type="default",
                    value=field["default"],
                    description=f"Default value: {field['default']}"
                )
            )
        
        # Order constraint
        if "order" in field:
            constraints.append(
                FieldConstraint(
                    type="order",
                    value=field["order"],
                    description=f"Order: {field['order']}"
                )
            )
        
        # Handle fixed type with size constraint
        field_type = field.get("type")
        if isinstance(field_type, dict) and field_type.get("type") == "fixed" and "size" in field_type:
            constraints.append(
                FieldConstraint(
                    type="size",
                    value=field_type["size"],
                    description=f"Fixed size: {field_type['size']} bytes"
                )
            )
        
        # Handle enum type with symbols constraint
        if isinstance(field_type, dict) and field_type.get("type") == "enum" and "symbols" in field_type:
            constraints.append(
                FieldConstraint(
                    type="enum",
                    value=field_type["symbols"],
                    description=f"Enum values: {field_type['symbols']}"
                )
            )
        
        return constraints
    
    def _extract_avro_type(self, avro_type: Any) -> Tuple[DataType, Optional[Dict[str, Any]]]:
        """
        Extract data type from Avro type definition.
        
        Args:
            avro_type: Avro type definition
            
        Returns:
            Tuple[DataType, Optional[Dict[str, Any]]]: Data type and type information
        """
        # Handle primitive types
        if isinstance(avro_type, str):
            return AVRO_TYPE_MAPPING.get(avro_type, DataType.UNKNOWN), None
        
        # Handle union types (like ["null", "string"])
        elif isinstance(avro_type, list):
            # Find the non-null type in the union
            non_null_types = [t for t in avro_type if t != "null"]
            
            if non_null_types:
                non_null_type = non_null_types[0]
                if isinstance(non_null_type, str):
                    return AVRO_TYPE_MAPPING.get(non_null_type, DataType.UNKNOWN), None
                elif isinstance(non_null_type, dict):
                    return self._extract_avro_type(non_null_type)
            
            return DataType.UNKNOWN, None
        
        # Handle complex types
        elif isinstance(avro_type, dict):
            complex_type = avro_type.get("type")
            
            if complex_type == "record":
                return DataType.OBJECT, {
                    "name": avro_type.get("name"),
                    "fields": avro_type.get("fields", []),
                }
            
            if complex_type == "enum":
                return DataType.ENUM, {
                    "name": avro_type.get("name"),
                    "symbols": avro_type.get("symbols", []),
                }
            
            if complex_type == "array":
                return DataType.ARRAY, {
                    "items": avro_type.get("items"),
                }
            
            if complex_type == "map":
                return DataType.OBJECT, {
                    "values": avro_type.get("values"),
                }
            
            if complex_type == "fixed":
                return DataType.BINARY, {
                    "name": avro_type.get("name"),
                    "size": avro_type.get("size"),
                }
            
            # Handle primitive types in complex form
            if complex_type in AVRO_TYPE_MAPPING:
                return AVRO_TYPE_MAPPING.get(complex_type, DataType.UNKNOWN), None
        
        return DataType.UNKNOWN, None
    
    def _is_nullable(self, avro_type: Any) -> bool:
        """
        Check if an Avro type is nullable.
        
        Args:
            avro_type: Avro type definition
            
        Returns:
            bool: Whether the type is nullable
        """
        # Check for union type with "null"
        if isinstance(avro_type, list) and "null" in avro_type:
            return True
        
        return False
    
    def _is_potential_primary_key(self, field_name: str) -> bool:
        """
        Determine if a field is a potential primary key.
        
        Args:
            field_name: Field name
            
        Returns:
            bool: True if the field could be a primary key
        """
        # Common primary key indicators
        indicators = [
            field_name.lower() == "id",
            field_name.lower().endswith("id") and len(field_name) > 2,
            field_name.lower() == "key",
            field_name.lower() == "primarykey",
            field_name.lower() == "primary_key",
            field_name.lower().startswith("uuid"),
        ]
        
        return any(indicators)
    
    def _format_avro_type(self, avro_type: Any) -> str:
        """
        Format Avro type for human-readable output.
        
        Args:
            avro_type: Avro type definition
            
        Returns:
            str: Formatted type string
        """
        if isinstance(avro_type, str):
            return avro_type
        
        elif isinstance(avro_type, list):
            return " or ".join(self._format_avro_type(t) for t in avro_type)
        
        elif isinstance(avro_type, dict):
            if avro_type.get("type") == "record":
                return f"record({avro_type.get('name', 'anonymous')})"
            
            if avro_type.get("type") == "enum":
                return f"enum({avro_type.get('name', 'anonymous')})"
            
            if avro_type.get("type") == "array":
                return f"array<{self._format_avro_type(avro_type.get('items', 'any'))}>"
            
            if avro_type.get("type") == "map":
                return f"map<string, {self._format_avro_type(avro_type.get('values', 'any'))}>"
            
            if avro_type.get("type") == "fixed":
                return f"fixed({avro_type.get('size', 0)})"
            
            # Simple type in complex form
            return str(avro_type.get("type", "unknown"))
        
        return "unknown"


# Export the parser class
parser = AvroParser()

def register_plugin():
    """Register the Avro schema parser plugin."""
    return {
        "format_id": "avro",
        "parser": parser,
        "priority": 60,  # Medium-high priority
        "description": "Avro schema parser",
        "format_info": {
            "id": "avro",
            "name": "Avro Schema",
            "description": "Apache Avro Schema Definition",
            "mime_types": ["application/json"],
            "extensions": [".avsc", ".avro.json"],
            "capabilities": {
                "schema_extraction": True,
                "type_inference": True,
                "relationship_detection": False,
                "streaming": False,
            },
            "examples": ['"type": "record"', '"namespace":', '"fields":'],
            "schema_type": "hierarchical",
            "version": "1.11.1",
        }
    }
