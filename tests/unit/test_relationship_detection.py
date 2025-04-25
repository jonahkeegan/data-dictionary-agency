"""
Unit tests for relationship detection functionality.
"""
import unittest
from unittest.mock import MagicMock, patch

from src.format_detection.models import DataType, FieldInfo, SchemaDetails
from src.relationship_detection.models import (
    RelationshipConfidence,
    RelationshipType,
    SchemaRelationship,
)
from src.relationship_detection.strategies.foreign_key import ForeignKeyRelationshipStrategy
from src.relationship_detection.strategies.name_based import NameBasedRelationshipStrategy
from src.relationship_detection.service import RelationshipDetectionService
from src.relationship_detection.utils.comparators import get_schema_id, are_types_compatible


class TestRelationshipModels(unittest.TestCase):
    """Tests for relationship detection models."""
    
    def test_relationship_type_enum(self):
        """Test that RelationshipType enum values are as expected."""
        self.assertEqual(RelationshipType.ONE_TO_ONE.value, "one_to_one")
        self.assertEqual(RelationshipType.ONE_TO_MANY.value, "one_to_many")
        self.assertEqual(RelationshipType.MANY_TO_ONE.value, "many_to_one")
        self.assertEqual(RelationshipType.MANY_TO_MANY.value, "many_to_many")
        self.assertEqual(RelationshipType.INHERITANCE.value, "inheritance")
        self.assertEqual(RelationshipType.COMPOSITION.value, "composition")
        self.assertEqual(RelationshipType.REFERENCE.value, "reference")
    
    def test_relationship_confidence(self):
        """Test RelationshipConfidence model."""
        confidence = RelationshipConfidence(
            score=0.8,
            factors={"factor1": 0.5, "factor2": 0.3},
            rationale="Test rationale",
            detection_method="test_method"
        )
        
        self.assertEqual(confidence.score, 0.8)
        self.assertEqual(confidence.factors, {"factor1": 0.5, "factor2": 0.3})
        self.assertEqual(confidence.rationale, "Test rationale")
        self.assertEqual(confidence.detection_method, "test_method")
    
    def test_schema_relationship(self):
        """Test SchemaRelationship model."""
        confidence = RelationshipConfidence(
            score=0.8,
            factors={"factor1": 0.5, "factor2": 0.3},
            rationale="Test rationale",
            detection_method="test_method"
        )
        
        relationship = SchemaRelationship(
            source_schema="source_schema",
            target_schema="target_schema",
            source_fields=["id"],
            target_fields=["source_id"],
            relationship_type=RelationshipType.ONE_TO_MANY,
            confidence=confidence,
            bidirectional=False,
            metadata={"key": "value"}
        )
        
        self.assertEqual(relationship.source_schema, "source_schema")
        self.assertEqual(relationship.target_schema, "target_schema")
        self.assertEqual(relationship.source_fields, ["id"])
        self.assertEqual(relationship.target_fields, ["source_id"])
        self.assertEqual(relationship.relationship_type, RelationshipType.ONE_TO_MANY)
        self.assertEqual(relationship.confidence, confidence)
        self.assertFalse(relationship.bidirectional)
        self.assertEqual(relationship.metadata, {"key": "value"})


class TestRelationshipDetectionService(unittest.TestCase):
    """Tests for RelationshipDetectionService."""
    
    def setUp(self):
        """Set up the test fixture."""
        self.service = RelationshipDetectionService()
        
        # Create mock schemas for testing
        self.user_schema = SchemaDetails(
            format="sql",
            fields=[
                FieldInfo(name="id", data_type=DataType.INTEGER, constraints=[], metadata={"primary_key": True}),
                FieldInfo(name="name", data_type=DataType.STRING, constraints=[], metadata={}),
                FieldInfo(name="email", data_type=DataType.STRING, constraints=[], metadata={"unique": True})
            ],
            primary_keys=["id"],
            unique_constraints=[["email"]],
            foreign_keys=[],
            metadata={"table_name": "users"}
        )
        
        self.post_schema = SchemaDetails(
            format="sql",
            fields=[
                FieldInfo(name="id", data_type=DataType.INTEGER, constraints=[], metadata={"primary_key": True}),
                FieldInfo(name="user_id", data_type=DataType.INTEGER, constraints=[], metadata={}),
                FieldInfo(name="title", data_type=DataType.STRING, constraints=[], metadata={})
            ],
            primary_keys=["id"],
            unique_constraints=[],
            foreign_keys=[
                {"columns": ["user_id"], "referenced_table": "users", "referenced_columns": ["id"]}
            ],
            metadata={"table_name": "posts"}
        )
    
    @patch('src.relationship_detection.service.TypeInferenceService')
    async def test_detect_relationships_empty_schemas(self, mock_type_inference_service):
        """Test detect_relationships with empty schemas."""
        # Setup
        mock_type_inference_service.return_value.enhance_schema.return_value = MagicMock()
        
        # Execute
        result = await self.service.detect_relationships([])
        
        # Verify
        self.assertEqual(len(result.relationships), 0)
        self.assertEqual(result.schema_coverage, {})
        self.assertEqual(result.metadata.get("status"), "no_schemas")
    
    @patch('src.relationship_detection.strategies.foreign_key.ForeignKeyRelationshipStrategy.detect')
    @patch('src.relationship_detection.service.TypeInferenceService')
    async def test_detect_relationships_with_foreign_key(self, mock_type_inference_service, mock_detect):
        """Test detect_relationships using foreign key strategy."""
        # Setup
        mock_type_inference_service.return_value.enhance_schema.side_effect = lambda x: x
        
        confidence = RelationshipConfidence(
            score=0.9,
            factors={"explicit_foreign_key": 0.9},
            rationale="Explicit foreign key definition",
            detection_method="foreign_key_analysis"
        )
        
        relationship = SchemaRelationship(
            source_schema="posts",
            target_schema="users",
            source_fields=["user_id"],
            target_fields=["id"],
            relationship_type=RelationshipType.MANY_TO_ONE,
            confidence=confidence,
            bidirectional=False,
            metadata={"foreign_key_name": "unnamed"}
        )
        
        mock_detect.return_value = [relationship]
        
        # Execute
        result = await self.service.detect_relationships([self.user_schema, self.post_schema])
        
        # Verify
        self.assertEqual(len(result.relationships), 1)
        self.assertEqual(result.relationships[0].source_schema, "posts")
        self.assertEqual(result.relationships[0].target_schema, "users")
        self.assertEqual(result.relationships[0].relationship_type, RelationshipType.MANY_TO_ONE)
        
        # Check that the strategy was called
        mock_detect.assert_called_once()


class TestRelationshipStrategies(unittest.TestCase):
    """Tests for relationship detection strategies."""
    
    def setUp(self):
        """Set up test fixture."""
        # Create schemas for testing
        self.user_schema = SchemaDetails(
            format="sql",
            fields=[
                FieldInfo(name="id", data_type=DataType.INTEGER, constraints=[], metadata={"primary_key": True}),
                FieldInfo(name="name", data_type=DataType.STRING, constraints=[], metadata={}),
                FieldInfo(name="email", data_type=DataType.STRING, constraints=[], metadata={"unique": True})
            ],
            primary_keys=["id"],
            unique_constraints=[["email"]],
            foreign_keys=[],
            metadata={"table_name": "users"}
        )
        
        self.post_schema = SchemaDetails(
            format="sql",
            fields=[
                FieldInfo(name="id", data_type=DataType.INTEGER, constraints=[], metadata={"primary_key": True}),
                FieldInfo(name="user_id", data_type=DataType.INTEGER, constraints=[], metadata={}),
                FieldInfo(name="title", data_type=DataType.STRING, constraints=[], metadata={})
            ],
            primary_keys=["id"],
            unique_constraints=[],
            foreign_keys=[
                {"columns": ["user_id"], "referenced_table": "users", "referenced_columns": ["id"]}
            ],
            metadata={"table_name": "posts"}
        )
    
    def test_foreign_key_strategy(self):
        """Test ForeignKeyRelationshipStrategy."""
        # Setup
        strategy = ForeignKeyRelationshipStrategy()
        
        # Execute
        relationships = strategy.detect([self.user_schema, self.post_schema])
        
        # Verify
        self.assertEqual(len(relationships), 1)
        self.assertEqual(relationships[0].source_schema, "posts")
        self.assertEqual(relationships[0].target_schema, "users")
        self.assertEqual(relationships[0].source_fields, ["user_id"])
        self.assertEqual(relationships[0].target_fields, ["id"])
        self.assertEqual(relationships[0].relationship_type, RelationshipType.MANY_TO_ONE)
        self.assertTrue(relationships[0].confidence.score > 0.8)  # High confidence for explicit FK
    
    def test_name_based_strategy(self):
        """Test NameBasedRelationshipStrategy with tables that have name-based relationships."""
        # Setup - Create schemas with name-based relationship
        comment_schema = SchemaDetails(
            format="sql",
            fields=[
                FieldInfo(name="id", data_type=DataType.INTEGER, constraints=[], metadata={"primary_key": True}),
                FieldInfo(name="post_id", data_type=DataType.INTEGER, constraints=[], metadata={}),
                FieldInfo(name="content", data_type=DataType.STRING, constraints=[], metadata={})
            ],
            primary_keys=["id"],
            unique_constraints=[],
            foreign_keys=[],  # No explicit foreign key
            metadata={"table_name": "comments"}
        )
        
        strategy = NameBasedRelationshipStrategy()
        
        # Execute
        relationships = strategy.detect([comment_schema, self.post_schema])
        
        # Verify
        self.assertTrue(len(relationships) > 0)
        
        # Finding the relationship from comments to posts
        post_relationships = [r for r in relationships if (r.source_schema == "comments" and r.target_schema == "posts") or
                             (r.source_schema == "posts" and r.target_schema == "comments")]
        
        self.assertTrue(len(post_relationships) > 0)
        relationship = post_relationships[0]
        
        # Verify field names are in the relationship
        if relationship.source_schema == "comments":
            self.assertTrue("post_id" in relationship.source_fields)
        else:
            self.assertTrue("post_id" in relationship.target_fields)


class TestUtilityFunctions(unittest.TestCase):
    """Tests for utility functions in the relationship_detection module."""
    
    def test_get_schema_id(self):
        """Test get_schema_id function."""
        # With table_name
        schema1 = SchemaDetails(
            format="sql",
            fields=[FieldInfo(name="id", data_type=DataType.INTEGER, constraints=[], metadata={})],
            primary_keys=[],
            unique_constraints=[],
            foreign_keys=[],
            metadata={"table_name": "test_table"}
        )
        self.assertEqual(get_schema_id(schema1), "test_table")
        
        # Without specific metadata
        schema2 = SchemaDetails(
            format="sql",
            fields=[FieldInfo(name="id", data_type=DataType.INTEGER, constraints=[], metadata={})],
            primary_keys=[],
            unique_constraints=[],
            foreign_keys=[],
            metadata={}
        )
        self.assertTrue("schema_1_id" in get_schema_id(schema2))
    
    def test_are_types_compatible(self):
        """Test are_types_compatible function."""
        # Same types
        self.assertTrue(are_types_compatible(DataType.INTEGER, DataType.INTEGER))
        self.assertTrue(are_types_compatible(DataType.STRING, DataType.STRING))
        
        # Compatible types
        self.assertTrue(are_types_compatible(DataType.INTEGER, DataType.FLOAT))
        self.assertTrue(are_types_compatible(DataType.STRING, DataType.ENUM))
        
        # Incompatible types
        self.assertFalse(are_types_compatible(DataType.INTEGER, DataType.STRING))
        self.assertFalse(are_types_compatible(DataType.BOOLEAN, DataType.DATE))


if __name__ == "__main__":
    unittest.main()
