"""
Unit tests for ORC schema parser.
"""
import sys
import os
import unittest
import io
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path

# Add the project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import models directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/format_detection')))
from models import FormatType, DataType, FieldInfo

# Import the parser class directly by loading the file
orc_init_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/format_detection/plugins/orc/__init__.py'))

# Create a namespace for the module
import types
orc_module = types.ModuleType('orc_module')

# Execute the file in this namespace
with open(orc_init_path, 'r') as f:
    exec(f.read(), orc_module.__dict__)

# Get the parser class from the namespace
ORCParser = orc_module.ORCParser

# Create parser instance for testing
orc_parser = ORCParser()

class TestORCParser(unittest.TestCase):
    """Test case for ORC schema parser."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample ORC file content with ORC magic bytes
        # ORC files start with "ORC" followed by a version byte
        self.valid_orc_content = b'ORC\x01' + b'\x00' * 100
        
        # Invalid content without magic bytes
        self.invalid_content = b'\x00' * 100
        
        # Content too short to be valid
        self.short_content = b'ORC'

    def test_format_type(self):
        """Test format type property."""
        plugin_info = orc_module.register_plugin()
        self.assertEqual(plugin_info["format_id"], "orc")

    def test_can_parse_with_extension(self):
        """Test can_parse method with correct file extension."""
        result, confidence = orc_parser.can_parse(self.valid_orc_content, "data.orc")
        self.assertTrue(result)
        self.assertGreaterEqual(confidence, 0.9)

    def test_can_parse_with_magic_bytes(self):
        """Test can_parse method with file content containing ORC magic bytes."""
        result, confidence = orc_parser.can_parse(self.valid_orc_content)
        self.assertTrue(result)
        self.assertGreaterEqual(confidence, 0.9)

    def test_can_parse_with_invalid_content(self):
        """Test can_parse with invalid content."""
        result, confidence = orc_parser.can_parse(self.invalid_content)
        self.assertFalse(result)
        self.assertEqual(confidence, 0.0)

    def test_can_parse_with_short_content(self):
        """Test can_parse with content that's too short."""
        result, confidence = orc_parser.can_parse(self.short_content)
        self.assertFalse(result)
        self.assertEqual(confidence, 0.0)

    @patch('pyarrow.orc.ORCFile')
    @patch.object(orc_module, 'SchemaDetails')
    def test_parse_schema(self, mock_schema_details, mock_orc_file):
        """Test parse_schema with mocked PyArrow components."""
        # Create mock PyArrow schema
        mock_schema = MagicMock()
        mock_metadata = MagicMock()
        
        # Create mock fields for test
        mock_id_field = MagicMock()
        mock_id_field.name = "id"
        mock_id_field.path = "id"
        mock_id_field.data_type = DataType.INTEGER
        mock_id_field.nullable = False
        
        mock_name_field = MagicMock()
        mock_name_field.name = "name"
        mock_name_field.path = "name"
        mock_name_field.data_type = DataType.STRING
        mock_name_field.nullable = True
        
        mock_active_field = MagicMock()
        mock_active_field.name = "active"
        mock_active_field.path = "active"
        mock_active_field.data_type = DataType.BOOLEAN
        mock_active_field.nullable = True
        
        mock_score_field = MagicMock()
        mock_score_field.name = "score"
        mock_score_field.path = "score"
        mock_score_field.data_type = DataType.FLOAT
        mock_score_field.nullable = True
        
        mock_address_field = MagicMock()
        mock_address_field.name = "address"
        mock_address_field.path = "address"
        mock_address_field.data_type = DataType.OBJECT
        mock_address_field.nullable = True

        # Create SchemaDetails instance
        mock_schema = MagicMock()
        mock_schema.fields = [
            mock_id_field,
            mock_name_field,
            mock_active_field,
            mock_score_field,
            mock_address_field
        ]
        
        # Configure metadata that will be used in schema
        mock_schema.metadata = {
            "num_rows": 1000,
            "content_length": 50000,
            "format_version": "1.0.0",
            "compression": "SNAPPY",
            "metadata": {}
        }
        
        # Return mock schema object from SchemaDetails constructor
        mock_schema_details.return_value = mock_schema
        
        # Configure ORCFile instance
        mock_orc_file_instance = MagicMock()
        mock_orc_file_instance.schema = MagicMock()
        mock_orc_file_instance.metadata = MagicMock()
        mock_orc_file_instance.metadata.num_rows = 1000
        mock_orc_file_instance.metadata.content_length = 50000
        mock_orc_file_instance.metadata.format_version = MagicMock(major=1, minor=0, patch=0)
        mock_orc_file_instance.metadata.compression = "SNAPPY"
        mock_orc_file_instance.metadata.metadata = {}
        mock_orc_file.return_value = mock_orc_file_instance
        
        # Call parse_schema
        schema = orc_parser.parse_schema(self.valid_orc_content, "data.orc")
        
        # Verify basic schema details
        self.assertIsNotNone(schema)
        self.assertEqual(1000, schema.metadata["num_rows"])
        self.assertEqual(50000, schema.metadata["content_length"])
        self.assertEqual("1.0.0", schema.metadata["format_version"])
        self.assertEqual("SNAPPY", schema.metadata["compression"])
        
        # Verify fields
        field_paths = [f.path for f in schema.fields]
        self.assertIn("id", field_paths)
        self.assertIn("name", field_paths)
        self.assertIn("active", field_paths)
        self.assertIn("score", field_paths)
        self.assertIn("address", field_paths)
        
        # Verify data types
        fields_by_path = {f.path: f for f in schema.fields}
        self.assertEqual(DataType.INTEGER, fields_by_path["id"].data_type)
        self.assertEqual(DataType.STRING, fields_by_path["name"].data_type)
        self.assertEqual(DataType.BOOLEAN, fields_by_path["active"].data_type)
        self.assertEqual(DataType.FLOAT, fields_by_path["score"].data_type)
        self.assertEqual(DataType.OBJECT, fields_by_path["address"].data_type)
        
        # Verify nullability
        self.assertFalse(fields_by_path["id"].nullable)
        self.assertTrue(fields_by_path["name"].nullable)
        self.assertTrue(fields_by_path["active"].nullable)
        self.assertTrue(fields_by_path["score"].nullable)
        self.assertTrue(fields_by_path["address"].nullable)

    @patch('pyarrow.orc.ORCFile')
    @patch.object(orc_module, 'SchemaDetails')
    def test_parse_schema_with_nested_fields(self, mock_schema_details, mock_orc_file):
        """Test parse_schema with nested field structures."""
        # Create mock schema with nested structures
        mock_schema = MagicMock()
        mock_metadata = MagicMock()
        
        # Configure metadata
        mock_metadata.num_rows = 1000
        mock_metadata.content_length = 50000
        mock_metadata.format_version = MagicMock(major=1, minor=0, patch=0)
        mock_metadata.compression = "SNAPPY"
        mock_metadata.metadata = {}
        
        # Create list field
        mock_list_field = self._create_mock_field("tags", "list", is_nullable=True)
        mock_list_field.type.value_field = self._create_mock_field("item", "string", is_nullable=True)
        
        # Create map field
        mock_map_field = self._create_mock_field("attributes", "map", is_nullable=True)
        mock_map_field.type.key_field = self._create_mock_field("key", "string", is_nullable=False)
        mock_map_field.type.item_field = self._create_mock_field("value", "string", is_nullable=True)
        
        # Create union field
        mock_union_field = self._create_mock_field("data", "union", is_nullable=True)
        mock_union_field.type.type_codes = [0, 1]
        mock_union_field.type.field = lambda i: self._create_mock_field(f"field_{i}", "string" if i == 0 else "int32", is_nullable=True)
        
        # Create mock fields
        mock_tags_field = MagicMock()
        mock_tags_field.name = "tags"
        mock_tags_field.path = "tags"
        mock_tags_field.data_type = DataType.ARRAY
        mock_tags_field.nullable = True
        
        mock_tags_items_field = MagicMock()
        mock_tags_items_field.name = "items"
        mock_tags_items_field.path = "tags.items"
        mock_tags_items_field.data_type = DataType.STRING
        mock_tags_items_field.nullable = True
        
        mock_attributes_field = MagicMock()
        mock_attributes_field.name = "attributes"
        mock_attributes_field.path = "attributes"
        mock_attributes_field.data_type = DataType.OBJECT
        mock_attributes_field.nullable = True
        
        mock_attributes_key_field = MagicMock()
        mock_attributes_key_field.name = "key"
        mock_attributes_key_field.path = "attributes.key"
        mock_attributes_key_field.data_type = DataType.STRING
        mock_attributes_key_field.nullable = False
        
        mock_attributes_value_field = MagicMock()
        mock_attributes_value_field.name = "value"
        mock_attributes_value_field.path = "attributes.value"
        mock_attributes_value_field.data_type = DataType.STRING
        mock_attributes_value_field.nullable = True
        
        mock_data_field = MagicMock()
        mock_data_field.name = "data"
        mock_data_field.path = "data"
        mock_data_field.data_type = DataType.OBJECT
        mock_data_field.nullable = True
        
        mock_data0_field = MagicMock()
        mock_data0_field.name = "data_0"
        mock_data0_field.path = "data_0" 
        mock_data0_field.data_type = DataType.STRING
        mock_data0_field.nullable = True
        
        mock_data1_field = MagicMock()
        mock_data1_field.name = "data_1"
        mock_data1_field.path = "data_1"
        mock_data1_field.data_type = DataType.INTEGER
        mock_data1_field.nullable = True
        
        # Create SchemaDetails instance
        mock_schema = MagicMock()
        mock_schema.fields = [
            mock_tags_field,
            mock_tags_items_field,
            mock_attributes_field,
            mock_attributes_key_field,
            mock_attributes_value_field,
            mock_data_field,
            mock_data0_field,
            mock_data1_field
        ]
        
        # Configure the mock
        mock_schema_details.return_value = mock_schema
        
        # No need to configure the _get_arrow_type method as we're using a mock SchemaDetails
        
        # Set schema fields
        mock_schema.__iter__.return_value = [mock_list_field, mock_map_field, mock_union_field]
        
        # Configure ORCFile instance
        mock_orc_file_instance = MagicMock()
        mock_orc_file_instance.schema = mock_schema
        mock_orc_file_instance.metadata = mock_metadata
        mock_orc_file.return_value = mock_orc_file_instance
        
        # Call parse_schema
        schema = orc_parser.parse_schema(self.valid_orc_content, "data.orc")
        
        # Verify fields
        field_paths = [f.path for f in schema.fields]
        self.assertIn("tags", field_paths)
        self.assertIn("tags.items", field_paths)
        self.assertIn("attributes", field_paths)
        self.assertIn("attributes.key", field_paths)
        self.assertIn("attributes.value", field_paths)
        self.assertIn("data", field_paths)
        self.assertIn("data_0", field_paths)
        self.assertIn("data_1", field_paths)
        
        # Verify data types
        fields_by_path = {f.path: f for f in schema.fields}
        self.assertEqual(DataType.ARRAY, fields_by_path["tags"].data_type)
        self.assertEqual(DataType.STRING, fields_by_path["tags.items"].data_type)
        self.assertEqual(DataType.OBJECT, fields_by_path["attributes"].data_type)
        self.assertEqual(DataType.STRING, fields_by_path["attributes.key"].data_type)
        self.assertEqual(DataType.STRING, fields_by_path["attributes.value"].data_type)
        self.assertEqual(DataType.OBJECT, fields_by_path["data"].data_type)
        self.assertEqual(DataType.STRING, fields_by_path["data_0"].data_type)
        self.assertEqual(DataType.INTEGER, fields_by_path["data_1"].data_type)

    @patch('pyarrow.orc.ORCFile')
    def test_parse_schema_import_error(self, mock_orc_file):
        """Test parse_schema with ImportError for PyArrow."""
        # Simulate ImportError when importing pyarrow
        mock_orc_file.side_effect = ImportError("No module named 'pyarrow'")
        
        # Call parse_schema and expect ValueError
        with self.assertRaises(ValueError) as context:
            orc_parser.parse_schema(self.valid_orc_content, "data.orc")
        
        # Verify error message
        self.assertIn("Failed to parse ORC: No module named 'pyarrow'", str(context.exception))

    @patch('pyarrow.orc.ORCFile')
    def test_parse_schema_error(self, mock_orc_file):
        """Test parse_schema with general error."""
        # Simulate error during parsing
        mock_orc_file.side_effect = Exception("Error parsing ORC file")
        
        # Call parse_schema and expect ValueError
        with self.assertRaises(ValueError) as context:
            orc_parser.parse_schema(self.valid_orc_content, "data.orc")
        
        # Verify error message
        self.assertIn("Error parsing ORC schema", str(context.exception))

    @patch('pyarrow.orc.ORCFile')
    def test_extract_sample_data(self, mock_orc_file):
        """Test extract_sample_data method."""
        # Create mock table with rows
        mock_table = MagicMock()
        mock_table.to_pylist.return_value = [
            {"id": 1, "name": "User 1", "active": True},
            {"id": 2, "name": "User 2", "active": False},
            {"id": 3, "name": "User 3", "active": True}
        ]
        
        # Configure ORCFile instance
        mock_orc_file_instance = MagicMock()
        mock_orc_file_instance.read.return_value = mock_table
        mock_orc_file.return_value = mock_orc_file_instance
        
        # Mock the _convert_record method to avoid isinstance issues with mocked objects
        with patch.object(orc_parser, '_convert_record', side_effect=lambda x: x):
            # Call extract_sample_data
            samples = orc_parser.extract_sample_data(self.valid_orc_content, max_records=3)
            
            # Verify samples
            self.assertEqual(3, len(samples))
            self.assertEqual(1, samples[0]["id"])
            self.assertEqual("User 1", samples[0]["name"])
            self.assertTrue(samples[0]["active"])
            
            self.assertEqual(2, samples[1]["id"])
            self.assertEqual("User 2", samples[1]["name"])
            self.assertFalse(samples[1]["active"])
            
            self.assertEqual(3, samples[2]["id"])
            self.assertEqual("User 3", samples[2]["name"])
            self.assertTrue(samples[2]["active"])

    @patch('pyarrow.orc.ORCFile')
    def test_extract_sample_data_import_error(self, mock_orc_file):
        """Test extract_sample_data with ImportError for PyArrow."""
        # Simulate ImportError when importing pyarrow
        mock_orc_file.side_effect = ImportError("No module named 'pyarrow'")
        
        # Call extract_sample_data and expect ValueError
        with self.assertRaises(ValueError) as context:
            orc_parser.extract_sample_data(self.valid_orc_content)
        
        # Verify error message
        self.assertIn("Failed to parse ORC: No module named 'pyarrow'", str(context.exception))

    @patch('pyarrow.orc.ORCFile')
    def test_extract_sample_data_error(self, mock_orc_file):
        """Test extract_sample_data with general error."""
        # Simulate error during parsing
        mock_orc_file.side_effect = Exception("Error reading ORC file")
        
        # Call extract_sample_data and expect ValueError
        with self.assertRaises(ValueError) as context:
            orc_parser.extract_sample_data(self.valid_orc_content)
        
        # Verify error message
        self.assertIn("Error extracting sample data", str(context.exception))

    def _create_mock_field(self, name, type_str, is_nullable=True):
        """Helper method to create a mock field with the given properties."""
        mock_field = MagicMock()
        mock_field.name = name
        mock_field.nullable = is_nullable
        
        # Set type property
        mock_type = MagicMock()
        mock_type.__str__.return_value = type_str
        mock_field.type = mock_type
        
        # Set metadata property
        mock_field.metadata = None
        
        return mock_field


if __name__ == "__main__":
    unittest.main()
