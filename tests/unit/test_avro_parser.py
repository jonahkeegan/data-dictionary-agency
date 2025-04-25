"""
Unit tests for Avro schema parser.
"""
import sys
import os
import tempfile
import unittest
from pathlib import Path

# Add the project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import directly to avoid plugin system issues
from src.format_detection.models import FormatType
from src.format_detection.plugins.avro.__init__ import AvroParser

# Create parser instance for testing
avro_parser = AvroParser()

class TestAvroParser(unittest.TestCase):
    """Test case for Avro schema parser."""

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

    def test_parse_schema_with_invalid_content(self):
        """Test parse_schema with invalid content."""
        content = b"This is not an Avro schema"
        schema = avro_parser.parse_schema("schema.avsc", content)
        
        # Should return an empty schema with error information
        self.assertEqual(0, len(schema.fields))
        self.assertTrue("error" in schema.metadata)

    def test_parse_schema_with_complex_types(self):
        """Test parse_schema with complex Avro types."""
        content = b"""
        {
            "type": "record",
            "name": "User",
            "namespace": "com.example",
            "fields": [
                {
                    "name": "address",
                    "type": {
                        "type": "record",
                        "name": "Address",
                        "fields": [
                            {"name": "street", "type": "string"},
                            {"name": "city", "type": "string"},
                            {"name": "zipcode", "type": "string"}
                        ]
                    }
                },
                {
                    "name": "tags",
                    "type": {
                        "type": "array",
                        "items": "string"
                    }
                },
                {
                    "name": "properties",
                    "type": {
                        "type": "map",
                        "values": "string"
                    }
                },
                {
                    "name": "status",
                    "type": {
                        "type": "enum",
                        "name": "Status",
                        "symbols": ["ACTIVE", "INACTIVE", "PENDING"]
                    }
                },
                {
                    "name": "hash",
                    "type": {
                        "type": "fixed",
                        "name": "MD5",
                        "size": 16
                    }
                }
            ]
        }
        """
        schema = avro_parser.parse_schema("schema.avsc", content)
        
        # Validate fields
        fields = {f.name: f for f in schema.fields}
        self.assertIn("address", fields)
        self.assertIn("tags", fields)
        self.assertIn("properties", fields)
        self.assertIn("status", fields)
        self.assertIn("hash", fields)
        
        # Validate types
        self.assertEqual("object", fields["address"].data_type)
        self.assertEqual("array", fields["tags"].data_type)
        self.assertEqual("object", fields["properties"].data_type)
        self.assertEqual("enum", fields["status"].data_type)
        self.assertEqual("binary", fields["hash"].data_type)
        
        # Check for nested fields
        nested_fields = [f for f in schema.fields if f.path.startswith("address.")]
        self.assertEqual(3, len(nested_fields))
        
        # Check constraints
        hash_constraints = next(f.constraints for f in schema.fields if f.name == "hash")
        self.assertTrue(any(c.type == "size" for c in hash_constraints))
        
        status_constraints = next(f.constraints for f in schema.fields if f.name == "status")
        self.assertTrue(any(c.type == "enum" for c in status_constraints))


if __name__ == "__main__":
    unittest.main()
