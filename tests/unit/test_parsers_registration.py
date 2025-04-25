"""
Unit tests for format detection plugin registration.
"""
import unittest
from src.format_detection.plugins import register_plugins

class TestParserRegistration(unittest.TestCase):
    """Test parser registration."""
    
    def test_parser_registration(self):
        """Test that all parsers are registered correctly."""
        # Register all plugins
        plugins = register_plugins()
        
        # Check if we have all expected format IDs
        expected_formats = {
            # Existing parsers
            'avro',
            'csv',
            'json',
            'sql',
            'xml',
            'yaml',
            
            # New parsers
            'graphql',
            'json_schema',
            'openapi',
            'parquet',
            'protobuf',
            'orc',
        }
        
        # Get registered format IDs
        registered_formats = set(plugins.keys())
        
        # Check if all expected formats are registered
        self.assertEqual(
            expected_formats, 
            registered_formats,
            f"Missing formats: {expected_formats - registered_formats}, "
            f"Extra formats: {registered_formats - expected_formats}"
        )
        
        # Check structure of each plugin registration
        for format_id, plugin_info in plugins.items():
            # Check required keys in plugin info
            self.assertIn('parser', plugin_info)
            self.assertIn('format_info', plugin_info)
            
            # Check required keys in format info
            format_info = plugin_info['format_info']
            self.assertIn('id', format_info)
            self.assertIn('name', format_info)
            self.assertIn('description', format_info)
            self.assertIn('capabilities', format_info)
            
            # Check capabilities
            capabilities = format_info['capabilities']
            self.assertIn('schema_extraction', capabilities)
            self.assertIn('type_inference', capabilities)
            
            # Check that parser has required methods
            parser = plugin_info['parser']
            self.assertTrue(hasattr(parser, 'can_parse'))
            self.assertTrue(hasattr(parser, 'parse_schema'))
            self.assertTrue(hasattr(parser, 'extract_sample_data'))

if __name__ == '__main__':
    unittest.main()
