"""
Unit tests for JSON Schema parser.
"""
import sys
import os
import json
import tempfile
import unittest
from pathlib import Path

# Add the project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.format_detection.plugins.json_schema import parser as json_schema_parser
from src.format_detection.models import FormatType

class TestJSONSchemaParser(unittest.TestCase):
    """Test case for JSON Schema parser."""

    def test_get_format_type(self):
        """Test get_format_type method."""
        self.assertEqual(json_schema_parser.get_format_type(), FormatType.JSON_SCHEMA)

    def test_can_parse_valid_json_schema(self):
        """Test can_parse method with valid JSON Schema."""
        content = json.dumps({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "User",
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "format": "uuid"
                },
                "name": {
                    "type": "string"
                }
            },
            "required": ["id", "name"]
        }).encode('utf-8')
        
        self.assertTrue(json_schema_parser.can_parse("user.schema.json", content))

    def test_can_parse_with_valid_extension(self):
        """Test can_parse with valid extension."""
        content = json.dumps({
            "title": "Test"
        }).encode('utf-8')
        
        self.assertTrue(json_schema_parser.can_parse("test.schema.json", content))
        self.assertTrue(json_schema_parser.can_parse("test.json-schema", content))

    def test_can_parse_with_schema_indicators(self):
        """Test can_parse with JSON Schema indicators."""
        # Test with multiple schema indicators
        content = json.dumps({
            "type": "object",
            "properties": {},
            "required": []
        }).encode('utf-8')
        
        self.assertTrue(json_schema_parser.can_parse("schema.json", content))
        
        # Test with different schema indicators
        content = json.dumps({
            "$id": "https://example.com/schema",
            "definitions": {
                "test": {"type": "string"}
            }
        }).encode('utf-8')
        
        self.assertTrue(json_schema_parser.can_parse("schema.json", content))

    def test_can_parse_with_invalid_content(self):
        """Test can_parse with invalid content."""
        content = b"This is not a JSON Schema"
        self.assertFalse(json_schema_parser.can_parse("schema.json", content))
        
        # Valid JSON but not a schema
        content = json.dumps({
            "name": "test",
            "value": 123
        }).encode('utf-8')
        
        self.assertFalse(json_schema_parser.can_parse("data.json", content))

    def test_can_parse_with_empty_content(self):
        """Test can_parse with empty content."""
        self.assertFalse(json_schema_parser.can_parse("schema.json", b""))

    def test_parse_schema_basic(self):
        """Test parse_schema with basic JSON Schema."""
        content = json.dumps({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "User",
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "User unique identifier"
                },
                "name": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 100,
                    "description": "User's full name"
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "User's email address"
                },
                "age": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 120,
                    "description": "User's age in years"
                },
                "isActive": {
                    "type": "boolean",
                    "description": "Whether the user is active"
                }
            },
            "required": ["id", "name", "email"]
        }).encode('utf-8')
        
        schema = json_schema_parser.parse_schema("user.schema.json", content)
        
        # Validate basic schema details
        self.assertIsNotNone(schema)
        self.assertEqual("json_schema", schema.metadata["schema_type"])
        self.assertEqual("User", schema.metadata["schema_title"])
        
        # Validate fields
        fields = {f.name: f for f in schema.fields}
        self.assertIn("id", fields)
        self.assertIn("name", fields)
        self.assertIn("email", fields)
        self.assertIn("age", fields)
        self.assertIn("isActive", fields)
        
        # Validate types
        self.assertEqual("uuid", fields["id"].data_type)
        self.assertEqual("string", fields["name"].data_type)
        self.assertEqual("string", fields["email"].data_type)
        self.assertEqual("integer", fields["age"].data_type)
        self.assertEqual("boolean", fields["isActive"].data_type)
        
        # Validate nullability
        self.assertFalse(fields["id"].nullable)
        self.assertFalse(fields["name"].nullable)
        self.assertFalse(fields["email"].nullable)
        self.assertTrue(fields["age"].nullable)
        self.assertTrue(fields["isActive"].nullable)
        
        # Validate constraints
        name_constraints = {c.type: c for c in fields["name"].constraints}
        self.assertIn("minLength", name_constraints)
        self.assertIn("maxLength", name_constraints)
        self.assertEqual(2, name_constraints["minLength"].value)
        self.assertEqual(100, name_constraints["maxLength"].value)
        
        age_constraints = {c.type: c for c in fields["age"].constraints}
        self.assertIn("minimum", age_constraints)
        self.assertIn("maximum", age_constraints)
        self.assertEqual(0, age_constraints["minimum"].value)
        self.assertEqual(120, age_constraints["maximum"].value)
        
        # Validate primary keys
        self.assertIn("id", schema.primary_keys)

    def test_parse_schema_with_nested_objects(self):
        """Test parse_schema with nested objects."""
        content = json.dumps({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "User",
            "type": "object",
            "properties": {
                "id": {
                    "type": "string"
                },
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {
                            "type": "string"
                        },
                        "city": {
                            "type": "string"
                        },
                        "postalCode": {
                            "type": "string"
                        }
                    },
                    "required": ["street", "city"]
                },
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        }).encode('utf-8')
        
        schema = json_schema_parser.parse_schema("user.schema.json", content)
        
        # Validate basic fields
        fields = {f.path: f for f in schema.fields}
        self.assertIn("id", fields)
        self.assertIn("address", fields)
        self.assertIn("address.street", fields)
        self.assertIn("address.city", fields)
        self.assertIn("address.postalCode", fields)
        self.assertIn("tags", fields)
        
        # Validate types
        self.assertEqual("object", fields["address"].data_type)
        self.assertEqual("string", fields["address.street"].data_type)
        self.assertEqual("array", fields["tags"].data_type)
        
        # Validate nullability of nested fields
        self.assertFalse(fields["address.street"].nullable)
        self.assertFalse(fields["address.city"].nullable)
        self.assertTrue(fields["address.postalCode"].nullable)

    def test_parse_schema_with_multiple_types(self):
        """Test parse_schema with multiple types per property."""
        content = json.dumps({
            "type": "object",
            "properties": {
                "value": {
                    "type": ["string", "null"],
                    "description": "A value that can be string or null"
                },
                "id": {
                    "type": ["integer", "string"]
                }
            }
        }).encode('utf-8')
        
        schema = json_schema_parser.parse_schema("schema.json", content)
        
        # Validate fields
        fields = {f.name: f for f in schema.fields}
        self.assertIn("value", fields)
        self.assertIn("id", fields)
        
        # Validate types (should use first non-null type)
        self.assertEqual("string", fields["value"].data_type)
        self.assertTrue(fields["value"].nullable)
        
        # For id, integer is the first type
        self.assertEqual("integer", fields["id"].data_type)

    def test_parse_schema_with_invalid_content(self):
        """Test parse_schema with invalid content."""
        content = b"This is not a JSON Schema"
        schema = json_schema_parser.parse_schema("schema.json", content)
        
        # Should return an empty schema with error information
        self.assertEqual(0, len(schema.fields))
        self.assertTrue("error" in schema.metadata)


if __name__ == "__main__":
    unittest.main()
