"""
Unit tests for XML parser.
"""
import sys
import os
import unittest
from pathlib import Path

# Add the project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import directly to avoid plugin system issues
from src.format_detection.models import FormatType

# Import the parser class directly from file to avoid plugin system issues
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/format_detection/plugins/xml')))
from src.format_detection.plugins.xml.__init__ import XMLParser

# Create parser instance for testing
xml_parser = XMLParser()


class TestXMLParser(unittest.TestCase):
    """Test case for XML parser."""

    def test_get_format_type(self):
        """Test get_format_type method."""
        self.assertEqual(xml_parser.get_format_type(), FormatType.XML)

    def test_can_parse_valid_xml(self):
        """Test can_parse method with valid XML."""
        content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <element>Text content</element>
            <element id="123">More text</element>
        </root>
        """
        self.assertTrue(xml_parser.can_parse("sample.xml", content))

    def test_can_parse_valid_xsd(self):
        """Test can_parse method with valid XSD schema."""
        content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:element name="root">
                <xs:complexType>
                    <xs:sequence>
                        <xs:element name="element" type="xs:string" minOccurs="1" maxOccurs="unbounded" />
                    </xs:sequence>
                </xs:complexType>
            </xs:element>
        </xs:schema>
        """
        self.assertTrue(xml_parser.can_parse("schema.xsd", content))

    def test_can_parse_with_valid_extension(self):
        """Test can_parse with valid extension."""
        content = b"<root></root>"  # Minimal content
        self.assertTrue(xml_parser.can_parse("data.xml", content))
        self.assertTrue(xml_parser.can_parse("schema.xsd", content))
        self.assertTrue(xml_parser.can_parse("image.svg", content))

    def test_can_parse_with_invalid_content(self):
        """Test can_parse with invalid content."""
        content = b"This is not an XML document"
        self.assertFalse(xml_parser.can_parse("file.txt", content))

    def test_can_parse_with_empty_content(self):
        """Test can_parse with empty content."""
        self.assertFalse(xml_parser.can_parse("file.xml", b""))

    def test_parse_schema_xml(self):
        """Test parse_schema with valid XML."""
        content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <users>
            <user id="1">
                <name>John Doe</name>
                <email>john@example.com</email>
                <age>30</age>
                <isActive>true</isActive>
                <address>
                    <street>123 Main St</street>
                    <city>New York</city>
                    <zipcode>10001</zipcode>
                </address>
            </user>
            <user id="2">
                <name>Jane Smith</name>
                <email>jane@example.com</email>
                <age>28</age>
                <isActive>false</isActive>
                <address>
                    <street>456 Park Ave</street>
                    <city>Boston</city>
                    <zipcode>02115</zipcode>
                </address>
            </user>
        </users>
        """
        schema = xml_parser.parse_schema("users.xml", content)
        
        # Validate basic schema details
        self.assertIsNotNone(schema)
        self.assertEqual("xml", schema.metadata["schema_type"])
        
        # Validate fields exist
        fields = {f.path: f for f in schema.fields}
        self.assertIn("users", fields)
        self.assertIn("users.user", fields)
        self.assertIn("users.user@id", fields)
        self.assertIn("users.user.name", fields)
        self.assertIn("users.user.email", fields)
        self.assertIn("users.user.age", fields)
        self.assertIn("users.user.isActive", fields)
        
        # Validate data types
        self.assertEqual("integer", fields["users.user@id"].data_type)
        self.assertEqual("string", fields["users.user.name"].data_type)
        self.assertEqual("string", fields["users.user.email"].data_type)
        self.assertEqual("integer", fields["users.user.age"].data_type)
        self.assertEqual("boolean", fields["users.user.isActive"].data_type)
        
        # Validate primary keys
        self.assertIn("id", schema.primary_keys)

    def test_parse_schema_xsd(self):
        """Test parse_schema with valid XSD schema."""
        content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:element name="users">
                <xs:complexType>
                    <xs:sequence>
                        <xs:element name="user" maxOccurs="unbounded">
                            <xs:complexType>
                                <xs:sequence>
                                    <xs:element name="name" type="xs:string" />
                                    <xs:element name="email" type="xs:string" />
                                    <xs:element name="age" type="xs:integer" />
                                    <xs:element name="isActive" type="xs:boolean" />
                                    <xs:element name="address">
                                        <xs:complexType>
                                            <xs:sequence>
                                                <xs:element name="street" type="xs:string" />
                                                <xs:element name="city" type="xs:string" />
                                                <xs:element name="zipcode" type="xs:string" />
                                            </xs:sequence>
                                        </xs:complexType>
                                    </xs:element>
                                </xs:sequence>
                                <xs:attribute name="id" type="xs:ID" use="required" />
                            </xs:complexType>
                        </xs:element>
                    </xs:sequence>
                </xs:complexType>
            </xs:element>
        </xs:schema>
        """
        schema = xml_parser.parse_schema("users.xsd", content)
        
        # Validate basic schema details
        self.assertIsNotNone(schema)
        self.assertEqual("xml", schema.metadata["schema_type"])
        self.assertTrue(schema.metadata["has_xsd_schema"])
        
        # Validate fields exist
        fields = {f.path: f for f in schema.fields}
        self.assertIn("users", fields)
        self.assertIn("users.user", fields)
        self.assertIn("users.user@id", fields)
        self.assertIn("users.user.name", fields)
        self.assertIn("users.user.email", fields)
        self.assertIn("users.user.age", fields)
        self.assertIn("users.user.isActive", fields)
        
        # Validate data types
        self.assertEqual("uuid", fields["users.user@id"].data_type)
        self.assertEqual("string", fields["users.user.name"].data_type)
        self.assertEqual("string", fields["users.user.email"].data_type)
        self.assertEqual("integer", fields["users.user.age"].data_type)
        self.assertEqual("boolean", fields["users.user.isActive"].data_type)
        
        # Check required constraint on ID field
        id_field = fields["users.user@id"]
        self.assertFalse(id_field.nullable)
        self.assertTrue(any(c.type == "required" for c in id_field.constraints))
        
        # Validate ID field is in primary keys
        self.assertIn("id", schema.primary_keys)

    def test_parse_schema_with_dtd(self):
        """Test parse_schema with XML that includes DTD."""
        content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE users [
            <!ELEMENT users (user*)>
            <!ELEMENT user (name, email, age, isActive)>
            <!ATTLIST user id ID #REQUIRED>
            <!ELEMENT name (#PCDATA)>
            <!ELEMENT email (#PCDATA)>
            <!ELEMENT age (#PCDATA)>
            <!ELEMENT isActive (#PCDATA)>
        ]>
        <users>
            <user id="u1">
                <name>John Doe</name>
                <email>john@example.com</email>
                <age>30</age>
                <isActive>true</isActive>
            </user>
        </users>
        """
        schema = xml_parser.parse_schema("users_with_dtd.xml", content)
        
        # Validate basic schema details
        self.assertIsNotNone(schema)
        self.assertEqual("xml", schema.metadata["schema_type"])
        self.assertTrue(schema.metadata["has_dtd"])
        
        # Validate that DTD elements were detected
        fields = {f.path: f for f in schema.fields}
        self.assertIn("users@id", fields) or self.assertIn("user@id", fields)
        
        # Validate ID field is in primary keys
        self.assertIn("id", schema.primary_keys)

    def test_parse_schema_with_dialect(self):
        """Test parse_schema with specific XML dialect."""
        # Test SVG dialect
        svg_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
            <rect x="10" y="10" width="80" height="80" fill="blue" />
            <circle cx="50" cy="50" r="30" fill="red" />
        </svg>
        """
        svg_schema = xml_parser.parse_schema("image.svg", svg_content)
        self.assertEqual("SVG", svg_schema.metadata["dialect"])
        
        # Test XHTML dialect
        xhtml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE html>
        <html xmlns="http://www.w3.org/1999/xhtml">
            <head><title>Test</title></head>
            <body><p>Hello World</p></body>
        </html>
        """
        xhtml_schema = xml_parser.parse_schema("page.xhtml", xhtml_content)
        self.assertEqual("XHTML", xhtml_schema.metadata["dialect"])

    def test_parse_schema_with_invalid_content(self):
        """Test parse_schema with invalid content."""
        content = b"This is not an XML document"
        schema = xml_parser.parse_schema("invalid.xml", content)
        
        # Should return an empty schema with error information
        self.assertEqual(0, len(schema.fields))
        self.assertIn("error", schema.metadata)

    def test_extract_sample_data(self):
        """Test extract_sample_data method."""
        content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <users>
            <user id="1">
                <name>John Doe</name>
                <email>john@example.com</email>
            </user>
            <user id="2">
                <name>Jane Smith</name>
                <email>jane@example.com</email>
            </user>
            <user id="3">
                <name>Bob Johnson</name>
                <email>bob@example.com</email>
            </user>
        </users>
        """
        samples = xml_parser.extract_sample_data("users.xml", content)
        
        # We should have at least one sample
        self.assertGreater(len(samples), 0)
        
        # Check the standard case - should have extracted user records
        if len(samples) > 1:
            # Check that we have user samples with attributes and child elements
            sample = samples[0]
            self.assertIn("@id", sample)
            self.assertIn("name", sample)
            self.assertIn("email", sample)


if __name__ == "__main__":
    unittest.main()
