"""
Unit tests for format detection service.
"""
import unittest
from unittest.mock import MagicMock, patch

from src.format_detection.models import FormatInfo
from src.format_detection.service import FormatDetectionService


class TestFormatDetectionService(unittest.TestCase):
    """Tests for FormatDetectionService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = FormatDetectionService()

    def test_init(self):
        """Test service initialization."""
        # Verify that the service has registered JSON and CSV formats
        self.assertIn("json", self.service.formats)
        self.assertIn("csv", self.service.formats)
        
        # Verify the JSON format info
        json_format = self.service.formats["json"]
        self.assertEqual(json_format.id, "json")
        self.assertEqual(json_format.name, "JSON")
        self.assertIn(".json", json_format.extensions)

    async def test_list_formats(self):
        """Test listing formats."""
        formats = await self.service.list_formats()
        
        # Verify we get a list of FormatInfo objects
        self.assertIsInstance(formats, list)
        self.assertTrue(all(isinstance(f, FormatInfo) for f in formats))
        
        # Verify at least JSON and CSV are present
        format_ids = [f.id for f in formats]
        self.assertIn("json", format_ids)
        self.assertIn("csv", format_ids)

    async def test_get_format(self):
        """Test getting a specific format."""
        # Test getting JSON format
        json_format = await self.service.get_format("json")
        self.assertIsNotNone(json_format)
        self.assertEqual(json_format.id, "json")
        self.assertEqual(json_format.name, "JSON")
        
        # Test getting non-existent format
        unknown_format = await self.service.get_format("unknown")
        self.assertIsNone(unknown_format)

    async def test_detect_format_by_extension(self):
        """Test format detection by file extension."""
        # Test JSON detection by extension
        result = await self.service.detect_format("test.json", b"{}")
        self.assertEqual(result.format_id, "json")
        self.assertGreaterEqual(result.confidence, 0.8)
        
        # Test CSV detection by extension
        result = await self.service.detect_format("test.csv", b"a,b,c\n1,2,3")
        self.assertEqual(result.format_id, "csv")
        self.assertGreaterEqual(result.confidence, 0.8)

    async def test_detect_format_by_content(self):
        """Test format detection by file content."""
        # Test JSON detection by content
        result = await self.service.detect_format("test.dat", b'{"name": "test"}')
        self.assertEqual(result.format_id, "json")
        
        # Test CSV detection by content
        result = await self.service.detect_format("test.dat", b"col1,col2,col3\nval1,val2,val3")
        self.assertEqual(result.format_id, "csv")
        
        # Test unknown format
        result = await self.service.detect_format("test.dat", b"This is plain text")
        self.assertIsNone(result.format_id)

    async def test_parse_file(self):
        """Test parsing a file."""
        # Test parsing JSON
        result = await self.service.parse_file("test.json", b'{"name": "test"}')
        self.assertEqual(result["format"], "json")
        self.assertIn("schema", result)
        
        # Test parsing CSV
        result = await self.service.parse_file("test.csv", b"col1,col2\nval1,val2")
        self.assertEqual(result["format"], "csv")
        self.assertIn("schema", result)
        
        # Test parsing with format detection
        result = await self.service.parse_file("test.dat", b'{"name": "test"}')
        self.assertEqual(result["format"], "json")
        
        # Test parsing unsupported format
        with self.assertRaises(ValueError):
            await self.service.parse_file("test.xyz", b"Unknown format")


if __name__ == "__main__":
    unittest.main()
