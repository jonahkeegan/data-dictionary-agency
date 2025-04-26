"""
Unit tests for Protocol Buffers schema parser.
"""
import sys
import os
import unittest
from pathlib import Path

# Add the project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import models directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/format_detection')))
from models import FormatType, DataType

# Import the parser class directly by loading the file
protobuf_init_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/format_detection/plugins/protobuf/__init__.py'))

# Create a namespace for the module
import types
protobuf_module = types.ModuleType('protobuf_module')

# Execute the file in this namespace
with open(protobuf_init_path, 'r') as f:
    exec(f.read(), protobuf_module.__dict__)

# Get the parser class from the namespace
ProtobufParser = protobuf_module.ProtobufParser

# Create parser instance for testing
protobuf_parser = ProtobufParser()

class TestProtobufParser(unittest.TestCase):
    """Test case for Protocol Buffers schema parser."""

    def test_format_type(self):
        """Test format type property."""
        self.assertEqual(protobuf_parser.get_format_type(), FormatType.PROTOBUF)

    def test_can_parse_valid_proto_with_extension(self):
        """Test can_parse method with valid proto file extension."""
        content = b"""
        syntax = "proto3";
        
        message Person {
            string name = 1;
            int32 id = 2;
            string email = 3;
        }
        """
        result, confidence = protobuf_parser.can_parse(content, "schema.proto")
        self.assertTrue(result)
        self.assertGreaterEqual(confidence, 0.9)

    def test_can_parse_valid_proto_without_extension(self):
        """Test can_parse method with valid proto content without file extension."""
        content = b"""
        syntax = "proto3";
        
        message Person {
            string name = 1;
            int32 id = 2;
            string email = 3;
        }
        """
        result, confidence = protobuf_parser.can_parse(content)
        self.assertTrue(result)
        self.assertGreaterEqual(confidence, 0.7)

    def test_can_parse_with_invalid_content(self):
        """Test can_parse with invalid content."""
        content = b"This is not a valid proto file"
        result, confidence = protobuf_parser.can_parse(content)
        self.assertFalse(result)
        self.assertLessEqual(confidence, 0.5)

    def test_can_parse_with_empty_content(self):
        """Test can_parse with empty content."""
        result, confidence = protobuf_parser.can_parse(b"")
        self.assertFalse(result)
        self.assertEqual(confidence, 0.0)

    def test_parse_schema_basic(self):
        """Test parse_schema with a basic proto definition."""
        content = b"""
        syntax = "proto3";
        
        package example;
        
        message Person {
            string name = 1;
            int32 id = 2;
            string email = 3;
            bool active = 4;
            repeated string phone_numbers = 5;
        }
        """
        schema = protobuf_parser.parse_schema(content, "schema.proto")
        
        # Validate basic schema details
        self.assertIsNotNone(schema)
        self.assertEqual("proto3", schema.metadata["syntax"])
        self.assertEqual("example", schema.metadata["package"])
        
        # Validate fields exist
        fields = {f.path: f for f in schema.fields}
        self.assertIn("Person.name", fields)
        self.assertIn("Person.id", fields)
        self.assertIn("Person.email", fields)
        self.assertIn("Person.active", fields)
        self.assertIn("Person.phone_numbers", fields)
        
        # Validate types
        self.assertEqual(DataType.STRING, fields["Person.name"].data_type)
        self.assertEqual(DataType.INTEGER, fields["Person.id"].data_type)
        self.assertEqual(DataType.STRING, fields["Person.email"].data_type)
        self.assertEqual(DataType.BOOLEAN, fields["Person.active"].data_type)
        self.assertEqual(DataType.ARRAY, fields["Person.phone_numbers"].data_type)
        
        # Validate metadata
        self.assertEqual("Person", fields["Person.name"].metadata["message"])
        self.assertEqual(1, fields["Person.name"].metadata["field_number"])
        self.assertTrue(fields["Person.phone_numbers"].metadata["is_repeated"])

    def test_parse_schema_with_nested_messages(self):
        """Test parse_schema with nested message definitions."""
        content = b"""
        syntax = "proto3";
        
        package example;
        
        message Person {
            string name = 1;
            int32 id = 2;
            
            message Address {
                string street = 1;
                string city = 2;
                string country = 3;
                int32 zip_code = 4;
            }
            
            Address address = 3;
            repeated Address previous_addresses = 4;
        }
        """
        schema = protobuf_parser.parse_schema(content, "schema.proto")
        
        # Validate nested fields exist
        fields = {f.path: f for f in schema.fields}
        self.assertIn("Person.name", fields)
        self.assertIn("Person.id", fields)
        self.assertIn("Person.address", fields)
        self.assertIn("Person.previous_addresses", fields)
        
        # Verify nested message fields
        self.assertEqual(DataType.OBJECT, fields["Person.address"].data_type)
        self.assertEqual(DataType.ARRAY, fields["Person.previous_addresses"].data_type)
        
        # Verify nested field paths
        nested_fields = [f for f in schema.fields if f.path.startswith("Person.Address.")]
        self.assertTrue(len(nested_fields) >= 4)  # Should have street, city, country, zip_code

    def test_parse_schema_with_enums(self):
        """Test parse_schema with enum fields."""
        content = b"""
        syntax = "proto3";
        
        package example;
        
        enum Status {
            UNKNOWN = 0;
            ACTIVE = 1;
            INACTIVE = 2;
            PENDING = 3;
        }
        
        message User {
            string name = 1;
            Status status = 2;
            
            enum Role {
                USER = 0;
                ADMIN = 1;
                MODERATOR = 2;
            }
            
            Role role = 3;
        }
        """
        schema = protobuf_parser.parse_schema(content, "schema.proto")
        
        # Validate enum fields
        enum_fields = [f for f in schema.fields if f.data_type == DataType.ENUM]
        self.assertTrue(len(enum_fields) >= 2)  # Should have Status and Role
        
        # Verify top-level enum
        status_field = next((f for f in schema.fields if f.path == "Status"), None)
        self.assertIsNotNone(status_field)
        self.assertEqual(DataType.ENUM, status_field.data_type)
        self.assertTrue("enum_values" in status_field.metadata)
        enum_values = status_field.metadata["enum_values"]
        self.assertIn("UNKNOWN", enum_values)
        self.assertIn("ACTIVE", enum_values)
        self.assertIn("INACTIVE", enum_values)
        self.assertIn("PENDING", enum_values)
        
        # Verify nested enum field
        user_role_field = next((f for f in schema.fields if f.path == "User.role"), None)
        self.assertIsNotNone(user_role_field)
        self.assertEqual(DataType.ENUM, user_role_field.data_type)

    def test_parse_schema_with_imports(self):
        """Test parse_schema with import statements."""
        content = b"""
        syntax = "proto3";
        
        package example;
        
        import "google/protobuf/timestamp.proto";
        import "other/file.proto";
        
        message Event {
            string name = 1;
            google.protobuf.Timestamp timestamp = 2;
            OtherType reference = 3;
        }
        """
        schema = protobuf_parser.parse_schema(content, "schema.proto")
        
        # Validate imports are detected
        self.assertIn("imports", schema.metadata)
        imports = schema.metadata["imports"]
        self.assertEqual(2, len(imports))
        self.assertIn("google/protobuf/timestamp.proto", imports)
        self.assertIn("other/file.proto", imports)
        
        # Validate dependencies
        self.assertEqual(2, len(schema.dependencies))

    def test_parse_schema_with_services(self):
        """Test parse_schema with service definitions."""
        content = b"""
        syntax = "proto3";
        
        package example;
        
        message HelloRequest {
            string name = 1;
        }
        
        message HelloResponse {
            string message = 1;
        }
        
        service Greeter {
            rpc SayHello (HelloRequest) returns (HelloResponse);
            rpc SayHelloAgain (HelloRequest) returns (HelloResponse);
        }
        """
        schema = protobuf_parser.parse_schema(content, "schema.proto")
        
        # Validate services are detected
        self.assertIn("services", schema.metadata)
        services = schema.metadata["services"]
        self.assertEqual(1, len(services))
        self.assertIn("Greeter", services)
        
        # Verify service methods
        all_services = schema.metadata.get("_services_details", [])
        greeter_service = next((s for s in all_services if s["name"] == "Greeter"), None)
        self.assertIsNotNone(greeter_service)
        
        methods = greeter_service.get("methods", [])
        self.assertEqual(2, len(methods))
        method_names = [m["name"] for m in methods]
        self.assertIn("SayHello", method_names)
        self.assertIn("SayHelloAgain", method_names)

    def test_parse_schema_with_map_type(self):
        """Test parse_schema with map type fields."""
        content = b"""
        syntax = "proto3";
        
        package example;
        
        message User {
            string name = 1;
            map<string, string> attributes = 2;
            map<int32, string> id_mapping = 3;
            map<string, Address> addresses = 4;
            
            message Address {
                string street = 1;
                string city = 2;
            }
        }
        """
        schema = protobuf_parser.parse_schema(content, "schema.proto")
        
        # Print fields for debugging
        print("\nDEBUG MAP FIELDS:")
        for field in schema.fields:
            if "User" in field.path:
                print(f"  {field.path}: {field.data_type} - {field.metadata}")
        
        # Validate map fields
        fields = {f.path: f for f in schema.fields}
        self.assertIn("User.attributes", fields)
        self.assertIn("User.id_mapping", fields)
        self.assertIn("User.addresses", fields)
        
        # Verify types
        self.assertEqual(DataType.OBJECT, fields["User.attributes"].data_type)
        self.assertEqual(DataType.OBJECT, fields["User.id_mapping"].data_type)
        self.assertEqual(DataType.OBJECT, fields["User.addresses"].data_type)
        
        # Verify metadata
        self.assertTrue("is_map" in fields["User.attributes"].metadata)
        self.assertTrue(fields["User.attributes"].metadata["is_map"])
        self.assertEqual("string", fields["User.attributes"].metadata.get("key_type"))
        self.assertEqual("string", fields["User.attributes"].metadata.get("value_type"))

    def test_parse_schema_with_oneof(self):
        """Test parse_schema with oneof fields."""
        content = b"""
        syntax = "proto3";
        
        package example;
        
        message Profile {
            string name = 1;
            
            oneof contact {
                string email = 2;
                string phone = 3;
                Address address = 4;
            }
            
            message Address {
                string street = 1;
                string city = 2;
            }
        }
        """
        schema = protobuf_parser.parse_schema(content, "schema.proto")
        
        # Validate oneof fields
        fields = {f.path: f for f in schema.fields}
        self.assertIn("Profile.email", fields)
        self.assertIn("Profile.phone", fields)
        self.assertIn("Profile.address", fields)
        
        # Verify oneof relationship in metadata
        self.assertEqual("contact", fields["Profile.email"].metadata.get("oneof_group"))
        self.assertEqual("contact", fields["Profile.phone"].metadata.get("oneof_group"))
        self.assertEqual("contact", fields["Profile.address"].metadata.get("oneof_group"))

    def test_extract_sample_data(self):
        """Test extract_sample_data method."""
        content = b"""
        syntax = "proto3";
        
        package example;
        
        message User {
            string name = 1;
            int32 id = 2;
            repeated string emails = 3;
        }
        
        message Order {
            int64 order_id = 1;
            string customer_id = 2;
            double total_amount = 3;
        }
        """
        samples = protobuf_parser.extract_sample_data(content)
        
        # Check that we have sample entries for both messages
        self.assertEqual(2, len(samples))
        
        # Verify message names
        message_names = [sample["message_name"] for sample in samples]
        self.assertIn("User", message_names)
        self.assertIn("Order", message_names)
        
        # Verify fields for User message
        user_sample = next(s for s in samples if s["message_name"] == "User")
        self.assertIn("name", user_sample["fields"])
        self.assertIn("id", user_sample["fields"])
        self.assertIn("emails", user_sample["fields"])
        
        # Verify fields for Order message
        order_sample = next(s for s in samples if s["message_name"] == "Order")
        self.assertIn("order_id", order_sample["fields"])
        self.assertIn("customer_id", order_sample["fields"])
        self.assertIn("total_amount", order_sample["fields"])


if __name__ == "__main__":
    unittest.main()
