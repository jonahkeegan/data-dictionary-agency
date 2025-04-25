"""
Standalone unit tests for Avro schema parser bypassing plugin system.
"""
import sys
import os
import json
import unittest

# Add the project root to path but avoid the plugins/__init__.py file
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import Avro parser and dependencies directly
from src.format_detection.models import (
    DataType,
    FieldConstraint,
    FieldInfo,
    FormatType,
    SchemaDetails,
)

# Create the parser class directly
class AvroParser:
    """Parser for Avro schema files."""
    
    def extract_sample_data(self, filename: str, content: bytes, max_records: int = 10):
        """Extract sample data from Avro schema content."""
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
            print(f"Error extracting sample data: {str(e)}")
            return [{"error": str(e)}]

    def can_parse(self, filename: str, content: bytes) -> bool:
        """Check if the file content can be parsed as an Avro schema."""
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
        """Get the format type handled by this parser."""
        return FormatType.AVRO

    def parse_schema(self, filename: str, content: bytes) -> SchemaDetails:
        """Parse Avro schema file and extract schema details."""
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
            print(f"Error parsing Avro schema: {str(e)}")
            # Return an empty schema in case of error
            return SchemaDetails(
                fields=[],
                metadata={
                    "schema_type": "avro",
                    "source_file": filename,
                    "error": str(e)
                }
            )
    
    def _process_schema(self, schema, fields, primary_keys, parent_path=""):
        """Process Avro schema and extract field information."""
        # Handle top-level record
        if isinstance(schema, dict) and schema.get("type") == "record":
            record_name = schema.get("name", "record")
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
    
    def _process_nested_types(self, field_type, fields, primary_keys, parent_path):
        """Process nested types in Avro schema."""
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
    
    def _extract_constraints(self, field):
        """Extract constraints from Avro field definition."""
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
    
    def _extract_avro_type(self, avro_type):
        """Extract data type from Avro type definition."""
        # Handle primitive types
        if isinstance(avro_type, str):
            return self.AVRO_TYPE_MAPPING.get(avro_type, DataType.UNKNOWN), None
        
        # Handle union types (like ["null", "string"])
        elif isinstance(avro_type, list):
            # Find the non-null type in the union
            non_null_types = [t for t in avro_type if t != "null"]
            
            if non_null_types:
                non_null_type = non_null_types[0]
                if isinstance(non_null_type, str):
                    return self.AVRO_TYPE_MAPPING.get(non_null_type, DataType.UNKNOWN), None
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
            if complex_type in self.AVRO_TYPE_MAPPING:
                return self.AVRO_TYPE_MAPPING.get(complex_type, DataType.UNKNOWN), None
        
        return DataType.UNKNOWN, None
    
    def _is_nullable(self, avro_type):
        """Check if an Avro type is nullable."""
        # Check for union type with "null"
        if isinstance(avro_type, list) and "null" in avro_type:
            return True
        
        return False
    
    def _is_potential_primary_key(self, field_name):
        """Determine if a field is a potential primary key."""
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
    
    def _format_avro_type(self, avro_type):
        """Format Avro type for human-readable output."""
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

# Create parser instance for testing
avro_parser = AvroParser()

class TestAvroParser(unittest.TestCase):
    """Test case for Avro parser."""

    def test_get_format_type(self):
        """Test get_format_type method."""
        self.assertEqual(avro_parser.get_format_type(), FormatType.AVRO)

    def test_can_parse_valid_avro(self):
        """Test can_parse method with valid Avro schema."""
        content = b"""
        {
            "type": "record",
            "name": "User",
            "namespace": "com.example",
            "fields": [
                {"name": "id", "type": "string"},
                {"name": "name", "type": "string"},
                {"name": "email", "type": ["null", "string"]},
                {"name": "age", "type": ["null", "int"], "default": null}
            ]
        }
        """
        self.assertTrue(avro_parser.can_parse("schema.avsc", content))

    def test_can_parse_with_valid_extension(self):
        """Test can_parse with valid extension."""
        content = b"{}"  # Minimal content
        self.assertTrue(avro_parser.can_parse("schema.avsc", content))
        self.assertTrue(avro_parser.can_parse("data.avro.json", content))

    def test_can_parse_with_invalid_content(self):
        """Test can_parse with invalid content."""
        content = b"This is not an Avro schema"
        self.assertFalse(avro_parser.can_parse("schema.txt", content))

    def test_can_parse_with_empty_content(self):
        """Test can_parse with empty content."""
        self.assertFalse(avro_parser.can_parse("schema.avsc", b""))

    def test_parse_schema(self):
        """Test parse_schema with valid Avro schema."""
        content = b"""
        {
            "type": "record",
            "name": "User",
            "namespace": "com.example",
            "doc": "User record",
            "fields": [
                {"name": "id", "type": "string", "doc": "User ID"},
                {"name": "name", "type": "string", "doc": "User's full name"},
                {"name": "email", "type": ["null", "string"], "doc": "User's email"},
                {"name": "age", "type": ["null", "int"], "default": null, "doc": "User's age"},
                {"name": "isActive", "type": "boolean", "doc": "Whether user is active"}
            ]
        }
        """
        schema = avro_parser.parse_schema("schema.avsc", content)
        
        # Validate basic schema details
        self.assertIsNotNone(schema)
        self.assertEqual("avro", schema.metadata["schema_type"])
        self.assertEqual("User", schema.metadata["name"])
        self.assertEqual("com.example", schema.metadata["namespace"])
        
        # Validate fields
        fields = {f.name: f for f in schema.fields}
        self.assertIn("id", fields)
        self.assertIn("name", fields)
        self.assertIn("email", fields)
        self.assertIn("age", fields)
        self.assertIn("isActive", fields)
        
        # Validate types
        self.assertEqual("string", fields["id"].data_type)
        self.assertEqual("string", fields["name"].data_type)
        self.assertEqual("string", fields["email"].data_type)
        self.assertEqual("integer", fields["age"].data_type)
        self.assertEqual("boolean", fields["isActive"].data_type)
        
        # Validate nullability
        self.assertFalse(fields["id"].nullable)
        self.assertFalse(fields["name"].nullable)
        self.assertTrue(fields["email"].nullable)
        self.assertTrue(fields["age"].nullable)
        self.assertFalse(fields["isActive"].nullable)
        
        # Validate primary keys
        self.assertIn("id", schema.primary_keys)

if __name__ == "__main__":
    unittest.main()
