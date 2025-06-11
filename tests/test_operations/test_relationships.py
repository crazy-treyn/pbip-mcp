"""Tests for relationship operations."""

import pytest
import json

from pbip_mcp.operations import OperationType


class TestRelationshipOperations:
    """Test cases for RelationshipOperations."""

    @pytest.mark.asyncio
    async def test_list_relationships(self, relationship_operations, test_project_path):
        """Test listing all relationships in the project."""
        args = {"project_path": test_project_path}
        
        result = await relationship_operations.execute(OperationType.LIST, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert "relationships" in data
        assert "count" in data
        
        # The test data may or may not have relationships, so just verify structure
        relationships = data["relationships"]
        for relationship in relationships:
            assert "name" in relationship
            assert "from_table" in relationship
            assert "from_column" in relationship
            assert "to_table" in relationship
            assert "to_column" in relationship
            assert "cardinality" in relationship
            assert "is_active" in relationship

    @pytest.mark.asyncio
    async def test_list_relationships_structure_validation(self, relationship_operations, test_project_path):
        """Test that relationship list has correct structure even if empty."""
        args = {"project_path": test_project_path}
        
        result = await relationship_operations.execute(OperationType.LIST, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert isinstance(data["relationships"], list)
        assert isinstance(data["count"], int)
        assert data["count"] == len(data["relationships"])

    @pytest.mark.asyncio
    async def test_list_relationships_cardinality_values(self, relationship_operations, test_project_path):
        """Test that relationships have valid cardinality values if any exist."""
        args = {"project_path": test_project_path}
        
        result = await relationship_operations.execute(OperationType.LIST, args)
        data = json.loads(result[0].text)
        
        valid_cardinalities = ["OneToMany", "ManyToOne", "OneToOne", "ManyToMany"]
        
        for relationship in data["relationships"]:
            if relationship["cardinality"] is not None:
                assert relationship["cardinality"] in valid_cardinalities

    @pytest.mark.asyncio
    async def test_list_relationships_cross_filtering_behavior(self, relationship_operations, test_project_path):
        """Test that relationships have valid cross-filtering behavior values if any exist."""
        args = {"project_path": test_project_path}
        
        result = await relationship_operations.execute(OperationType.LIST, args)
        data = json.loads(result[0].text)
        
        valid_behaviors = ["Automatic", "OneDirection", "BothDirections"]
        
        for relationship in data["relationships"]:
            if "cross_filtering_behavior" in relationship and relationship["cross_filtering_behavior"] is not None:
                assert relationship["cross_filtering_behavior"] in valid_behaviors

    @pytest.mark.asyncio
    async def test_list_relationships_active_status(self, relationship_operations, test_project_path):
        """Test that relationships have boolean is_active values."""
        args = {"project_path": test_project_path}
        
        result = await relationship_operations.execute(OperationType.LIST, args)
        data = json.loads(result[0].text)
        
        for relationship in data["relationships"]:
            assert isinstance(relationship["is_active"], bool)

    @pytest.mark.asyncio
    async def test_list_relationships_table_references(self, relationship_operations, test_project_path, expected_tables):
        """Test that relationship table references are valid if any exist."""
        args = {"project_path": test_project_path}
        
        result = await relationship_operations.execute(OperationType.LIST, args)
        data = json.loads(result[0].text)
        
        for relationship in data["relationships"]:
            # Verify from_table and to_table reference valid tables
            assert relationship["from_table"] in expected_tables or relationship["from_table"] == ""
            assert relationship["to_table"] in expected_tables or relationship["to_table"] == ""

    @pytest.mark.asyncio
    async def test_list_relationships_invalid_project_path(self, relationship_operations):
        """Test listing relationships with invalid project path fails."""
        args = {"project_path": "/nonexistent/path"}
        
        result = await relationship_operations.execute(OperationType.LIST, args)
        assert len(result) == 1
        assert "Error:" in result[0].text

    @pytest.mark.asyncio
    async def test_list_relationships_missing_semantic_model(self, relationship_operations, temp_dir):
        """Test listing relationships when semantic model is missing fails."""
        # Create a directory without semantic model
        empty_dir = temp_dir / "empty_project"
        empty_dir.mkdir()
        
        args = {"project_path": str(empty_dir)}
        
        result = await relationship_operations.execute(OperationType.LIST, args)
        assert len(result) == 1
        assert "Error:" in result[0].text

    @pytest.mark.asyncio
    async def test_relationships_name_uniqueness(self, relationship_operations, test_project_path):
        """Test that relationship names are unique if any exist."""
        args = {"project_path": test_project_path}
        
        result = await relationship_operations.execute(OperationType.LIST, args)
        data = json.loads(result[0].text)
        
        relationship_names = [rel["name"] for rel in data["relationships"] if rel["name"]]
        assert len(relationship_names) == len(set(relationship_names))  # All names should be unique

    @pytest.mark.asyncio
    async def test_relationships_column_references_exist(self, relationship_operations, test_project_path):
        """Test that column references in relationships are non-empty if any exist."""
        args = {"project_path": test_project_path}
        
        result = await relationship_operations.execute(OperationType.LIST, args)
        data = json.loads(result[0].text)
        
        for relationship in data["relationships"]:
            # If we have table references, we should have column references too
            if relationship["from_table"] and relationship["to_table"]:
                assert relationship["from_column"], f"Missing from_column in relationship: {relationship['name']}"
                assert relationship["to_column"], f"Missing to_column in relationship: {relationship['name']}"

    @pytest.mark.asyncio
    async def test_unknown_operation(self, relationship_operations, test_project_path):
        """Test that unknown operations return appropriate error."""
        result = await relationship_operations.execute("unknown_operation", {"project_path": test_project_path})
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "unknown operation" in result[0].text.lower()