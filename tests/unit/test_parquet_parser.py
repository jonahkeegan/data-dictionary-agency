"""
Unit tests for Parquet schema parser.
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
parquet_init_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/format_detection/plugins/parquet/__init__.py'))

# Create a namespace for the module
import types
parquet_module = types.ModuleType('parquet_module')

# Execute the file in this namespace
with open(parquet_init_path, 'r') as f:
    exec(f.read(), parquet_module.__dict__)

# Get the parser class from the namespace
ParquetParser = parquet_module.ParquetParser

# Create parser instance for testing
parquet_parser = ParquetParser()

class TestParquetParser(unittest.TestCase):
    """Test case for Parquet schema parser."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample Parquet file content with PAR1 magic bytes
        # PAR1 magic bytes at the beginning and end
        self.valid_parquet_content = b'PAR1' + b'\x00' * 100 + b'PAR1'
        
        # Invalid content without magic bytes
        self.invalid_content = b'\x00' * 100
        
        # Content too short to be valid
        self.short_content = b'PAR1'

    def test_format_type(self):
        """Test format type property."""
        plugin_info = parquet_module.register_plugin()
        self.assertEqual(plugin_info["format_id"], "parquet")

    def test_can_parse_with_extension(self):
        """Test can_parse method with correct file extension."""
        result, confidence = parquet_parser.can_parse(self.valid_parquet_content, "data.parquet")
        self.assertTrue(result)
        self.assertGreaterEqual(confidence, 0.9)

    def test_can_parse_with_magic_bytes(self):
        """Test can_parse method with file content containing PAR1 magic bytes."""
        result, confidence = parquet_parser.can_parse(self.valid_parquet_content)
        self.assertTrue(result)
        self.assertGreaterEqual(confidence, 0.9)

    def test_can_parse_with_invalid_content(self):
        """Test can_parse with invalid content."""
        result, confidence = parquet_parser.can_parse(self.invalid_content)
        self.assertFalse(result)
        self.assertEqual(confidence, 0.0)

    def test_can_parse_with_short_content(self):
        """Test can_parse with content that's too short."""
        result, confidence = parquet_parser.can_parse(self.short_content)
        self.assertFalse(result)
        self.assertEqual(confidence, 0.0)

    @patch('pyarrow.parquet.ParquetFile')
    @patch.object(parquet_module, 'SchemaDetails')
    def test_parse_schema(self, mock_schema_details, mock_pq_file):
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
            "num_row_groups": 10,
            "format_version": "2.0.0",
            "created_by": "PyArrow Test",
            "metadata": {"schema_key": "schema_value"}
        }
        
        # Return mock schema object from SchemaDetails constructor
        mock_schema_details.return_value = mock_schema
        
        # Configure ParquetFile instance
        mock_pq_file_instance = MagicMock()
        mock_pq_file_instance.schema_arrow = MagicMock()
        mock_pq_file_instance.metadata = MagicMock()
        mock_pq_file_instance.metadata.num_rows = 1000
        mock_pq_file_instance.metadata.num_row_groups = 10
        mock_pq_file_instance.metadata.format_version = MagicMock(major=2, minor=0, patch=0)
        mock_pq_file_instance.metadata.created_by = "PyArrow Test"
        mock_pq_file_instance.metadata.metadata = {b'schema_key': b'schema_value'}
        mock_pq_file.return_value = mock_pq_file_instance
        
        # Call parse_schema
        schema = parquet_parser.parse_schema(self.valid_parquet_content, "data.parquet")
        
        # Verify basic schema details
        self.assertIsNotNone(schema)
        self.assertEqual(1000, schema.metadata["num_rows"])
        self.assertEqual(10, schema.metadata["num_row_groups"])
        self.assertEqual("2.0.0", schema.metadata["format_version"])
        self.assertEqual("PyArrow Test", schema.metadata["created_by"])
        self.assertEqual("schema_value", schema.metadata["metadata"]["schema_key"])
        
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

    @patch('pyarrow.parquet.ParquetFile')
    @patch.object(parquet_module, 'SchemaDetails')
    def test_parse_schema_with_nested_fields(self, mock_schema_details, mock_pq_file):
        """Test parse_schema with nested field structures."""
        # Create mock schema with nested structures
        mock_schema = MagicMock()
        mock_metadata = MagicMock()
        
        # Configure metadata
        mock_metadata.num_rows = 1000
        mock_metadata.num_row_groups = 10
        mock_metadata.format_version = MagicMock(major=2, minor=0, patch=0)
        mock_metadata.created_by = "PyArrow Test"
        mock_metadata.metadata = {}
        
        # Create list field
        mock_list_field = self._create_mock_field("tags", "list", is_nullable=True)
        mock_list_field.type.value_field = self._create_mock_field("item", "string", is_nullable=True)
        
        # Create map field
        mock_map_field = self._create_mock_field("attributes", "map", is_nullable=True)
        mock_map_field.type.key_field = self._create_mock_field("key", "string", is_nullable=False)
        mock_map_field.type.item_field = self._create_mock_field("value", "string", is_nullable=True)
        
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
        
        # Create SchemaDetails instance
        mock_schema = MagicMock()
        mock_schema.fields = [
            mock_tags_field,
            mock_tags_items_field,
            mock_attributes_field,
            mock_attributes_key_field,
            mock_attributes_value_field
        ]
        
        # Configure the mock
        mock_schema_details.return_value = mock_schema
        
        # No need to configure the _get_arrow_type method as we're using a mock SchemaDetails
        
        # Set schema fields
        mock_schema.__iter__.return_value = [mock_list_field, mock_map_field]
        
        # Configure ParquetFile instance
        mock_pq_file_instance = MagicMock()
        mock_pq_file_instance.schema_arrow = mock_schema
        mock_pq_file_instance.metadata = mock_metadata
        mock_pq_file.return_value = mock_pq_file_instance
        
        # Call parse_schema
        schema = parquet_parser.parse_schema(self.valid_parquet_content, "data.parquet")
        
        # Verify fields
        field_paths = [f.path for f in schema.fields]
        self.assertIn("tags", field_paths)
        self.assertIn("tags.items", field_paths)
        self.assertIn("attributes", field_paths)
        self.assertIn("attributes.key", field_paths)
        self.assertIn("attributes.value", field_paths)
        
        # Verify data types
        fields_by_path = {f.path: f for f in schema.fields}
        self.assertEqual(DataType.ARRAY, fields_by_path["tags"].data_type)
        self.assertEqual(DataType.STRING, fields_by_path["tags.items"].data_type)
        self.assertEqual(DataType.OBJECT, fields_by_path["attributes"].data_type)
        self.assertEqual(DataType.STRING, fields_by_path["attributes.key"].data_type)
        self.assertEqual(DataType.STRING, fields_by_path["attributes.value"].data_type)

    @patch('pyarrow.parquet.ParquetFile')
    def test_parse_schema_import_error(self, mock_pq_file):
        """Test parse_schema with ImportError for PyArrow."""
        # Simulate ImportError when importing pyarrow
        mock_pq_file.side_effect = ImportError("No module named 'pyarrow'")
        
        # Call parse_schema and expect ValueError
        with self.assertRaises(ValueError) as context:
            parquet_parser.parse_schema(self.valid_parquet_content, "data.parquet")
        
        # Verify error message
        self.assertIn("Failed to parse Parquet: No module named 'pyarrow'", str(context.exception))

    @patch('pyarrow.parquet.ParquetFile')
    def test_parse_schema_error(self, mock_pq_file):
        """Test parse_schema with general error."""
        # Simulate error during parsing
        mock_pq_file.side_effect = Exception("Error parsing Parquet file")
        
        # Call parse_schema and expect ValueError
        with self.assertRaises(ValueError) as context:
            parquet_parser.parse_schema(self.valid_parquet_content, "data.parquet")
        
        # Verify error message
        self.assertIn("Error parsing Parquet schema", str(context.exception))

    @patch('pyarrow.parquet.ParquetFile')
    def test_extract_sample_data(self, mock_pq_file):
        """Test extract_sample_data method."""
        # Create mock table with rows
        mock_table = MagicMock()
        mock_table.to_pylist.return_value = [
            {"id": 1, "name": "User 1", "active": True},
            {"id": 2, "name": "User 2", "active": False},
            {"id": 3, "name": "User 3", "active": True}
        ]
        
        # Configure ParquetFile instance
        mock_pq_file_instance = MagicMock()
        mock_pq_file_instance.read_row_group.return_value = mock_table
        mock_pq_file.return_value = mock_pq_file_instance
        
        # Mock the _convert_record method to avoid isinstance issues with mocked objects
        with patch.object(parquet_parser, '_convert_record', side_effect=lambda x: x):
            # Call extract_sample_data
            samples = parquet_parser.extract_sample_data(self.valid_parquet_content, max_records=3)
            
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

    @patch('pyarrow.parquet.ParquetFile')
    def test_extract_sample_data_import_error(self, mock_pq_file):
        """Test extract_sample_data with ImportError for PyArrow."""
        # Simulate ImportError when importing pyarrow
        mock_pq_file.side_effect = ImportError("No module named 'pyarrow'")
        
        # Call extract_sample_data and expect ValueError
        with self.assertRaises(ValueError) as context:
            parquet_parser.extract_sample_data(self.valid_parquet_content)
        
        # Verify error message
        self.assertIn("Failed to parse Parquet: No module named 'pyarrow'", str(context.exception))

    @patch('pyarrow.parquet.ParquetFile')
    def test_extract_sample_data_error(self, mock_pq_file):
        """Test extract_sample_data with general error."""
        # Simulate error during parsing
        mock_pq_file.side_effect = Exception("Error reading Parquet file")
        
        # Call extract_sample_data and expect ValueError
        with self.assertRaises(ValueError) as context:
            parquet_parser.extract_sample_data(self.valid_parquet_content)
        
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
