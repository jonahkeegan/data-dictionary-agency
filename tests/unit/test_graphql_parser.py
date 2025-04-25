"""
Unit tests for GraphQL schema parser.
"""
import sys
import os
import tempfile
import unittest
from pathlib import Path

# Add the project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.format_detection.plugins.graphql import parser as graphql_parser
from src.format_detection.models import FormatType

class TestGraphQLParser(unittest.TestCase):
    """Test case for GraphQL schema parser."""

    def test_get_format_type(self):
        """Test get_format_type method."""
        self.assertEqual(graphql_parser.get_format_type(), FormatType.GRAPHQL)

    def test_can_parse_valid_graphql(self):
        """Test can_parse method with valid GraphQL schema."""
        content = b"""
        type User {
            id: ID!
            name: String!
            email: String
            posts: [Post!]
        }

        type Post {
            id: ID!
            title: String!
            content: String!
            author: User!
            createdAt: String
        }

        type Query {
            getUser(id: ID!): User
            getPosts: [Post!]!
        }
        """
        self.assertTrue(graphql_parser.can_parse("schema.graphql", content))

    def test_can_parse_with_valid_extension(self):
        """Test can_parse with valid extension."""
        content = b"# This is a valid empty GraphQL file"
        self.assertTrue(graphql_parser.can_parse("schema.graphql", content))
        self.assertTrue(graphql_parser.can_parse("schema.gql", content))

    def test_can_parse_with_invalid_content(self):
        """Test can_parse with invalid content."""
        content = b"This is not a GraphQL schema"
        self.assertFalse(graphql_parser.can_parse("schema.txt", content))

    def test_can_parse_with_empty_content(self):
        """Test can_parse with empty content."""
        self.assertFalse(graphql_parser.can_parse("schema.graphql", b""))

    def test_parse_schema(self):
        """Test parse_schema with valid GraphQL schema."""
        content = b"""
        # User entity
        type User {
            id: ID!
            name: String!
            email: String
            age: Int
            isActive: Boolean!
        }
        """
        schema = graphql_parser.parse_schema("schema.graphql", content)
        
        # Validate basic schema details
        self.assertIsNotNone(schema)
        self.assertEqual("graphql", schema.metadata["schema_type"])
        
        # Validate fields
        fields = {f.name: f for f in schema.fields}
        self.assertIn("id", fields)
        self.assertIn("name", fields)
        self.assertIn("email", fields)
        self.assertIn("age", fields)
        self.assertIn("isActive", fields)
        
        # Validate types
        self.assertEqual("string", fields["name"].data_type)
        self.assertEqual("integer", fields["age"].data_type)
        self.assertEqual("boolean", fields["isActive"].data_type)
        self.assertEqual("uuid", fields["id"].data_type)
        
        # Validate nullability
        self.assertFalse(fields["id"].nullable)
        self.assertFalse(fields["name"].nullable)
        self.assertTrue(fields["email"].nullable)
        
        # Validate primary keys
        self.assertIn("id", schema.primary_keys)

    def test_parse_schema_with_invalid_content(self):
        """Test parse_schema with invalid content."""
        content = b"This is not a GraphQL schema"
        schema = graphql_parser.parse_schema("schema.graphql", content)
        
        # Should return an empty schema with error information
        self.assertEqual(0, len(schema.fields))
        self.assertTrue("error" in schema.metadata)

    def test_parse_schema_with_complex_types(self):
        """Test parse_schema with complex GraphQL types."""
        content = b"""
        type User {
            friends: [User]
            settings: UserSettings
        }
        
        type UserSettings {
            theme: String
            notifications: Boolean!
        }
        """
        schema = graphql_parser.parse_schema("schema.graphql", content)
        
        # Validate fields
        fields = {f.name: f for f in schema.fields}
        self.assertIn("friends", fields)
        self.assertIn("settings", fields)
        
        # Validate types
        self.assertEqual("array", fields["friends"].data_type)
        self.assertEqual("object", fields["settings"].data_type)


if __name__ == "__main__":
    unittest.main()
