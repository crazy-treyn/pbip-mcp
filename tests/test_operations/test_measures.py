"""Tests for measure operations."""

import pytest
import json
from pathlib import Path

from pbip_mcp.operations import OperationType


class TestMeasureOperations:
    """Test cases for MeasureOperations."""

    @pytest.mark.asyncio
    async def test_list_measures_all_tables(self, measure_operations, test_project_path):
        """Test listing all measures across all tables."""
        args = {"project_path": test_project_path}
        
        result = await measure_operations.execute(OperationType.LIST, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert "measures" in data
        assert "count" in data
        assert data["count"] == 3  # Expected number of measures in test data
        
        # Verify measure structure
        measures = data["measures"]
        assert all("name" in measure for measure in measures)
        assert all("table_name" in measure for measure in measures)
        assert all("expression" in measure for measure in measures)

    @pytest.mark.asyncio
    async def test_list_measures_specific_table(self, measure_operations, test_project_path):
        """Test listing measures for a specific table."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact"
        }
        
        result = await measure_operations.execute(OperationType.LIST, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        measures = data["measures"]
        assert all(measure["table_name"] == "Fact" for measure in measures)
        assert len(measures) == 3  # Fact table should have 3 measures

    @pytest.mark.asyncio
    async def test_add_measure_success(self, measure_operations, test_project_path, sample_measure_args):
        """Test successfully adding a new measure."""
        args = {**sample_measure_args, "project_path": test_project_path}
        
        result = await measure_operations.execute(OperationType.ADD, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["table_name"] == "Fact"
        assert data["measure_name"] == "Test Measure"
        assert data["action"] == "added"
        
        # Verify measure was actually added by listing measures
        list_args = {"project_path": test_project_path, "table_name": "Fact"}
        list_result = await measure_operations.execute(OperationType.LIST, list_args)
        list_data = json.loads(list_result[0].text)
        
        measure_names = [m["name"] for m in list_data["measures"]]
        assert "Test Measure" in measure_names

    @pytest.mark.asyncio
    async def test_add_measure_duplicate_name(self, measure_operations, test_project_path):
        """Test adding a measure with a duplicate name fails."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "measure_name": "PlaceholderMeasure",  # Already exists
            "expression": "SUM(Fact[Value])"
        }
        
        result = await measure_operations.execute(OperationType.ADD, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "already exists" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_add_measure_invalid_table(self, measure_operations, test_project_path, sample_measure_args):
        """Test adding a measure to a non-existent table fails."""
        args = {**sample_measure_args, "project_path": test_project_path, "table_name": "NonExistentTable"}
        
        result = await measure_operations.execute(OperationType.ADD, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_add_measure_invalid_dax(self, measure_operations, test_project_path, sample_measure_args):
        """Test adding a measure with invalid DAX expression fails."""
        args = {**sample_measure_args, "project_path": test_project_path, "expression": "SUM(Fact[Value"}  # Missing closing bracket
        
        result = await measure_operations.execute(OperationType.ADD, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "invalid" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_measure_expression(self, measure_operations, test_project_path):
        """Test updating a measure's expression."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "measure_name": "PlaceholderMeasure",
            "expression": "SUM(Fact[Revenue]) * 2"
        }
        
        result = await measure_operations.execute(OperationType.UPDATE, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["table_name"] == "Fact"
        assert data["measure_name"] == "PlaceholderMeasure"
        assert "expression" in data["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_measure_format_string(self, measure_operations, test_project_path):
        """Test updating a measure's format string."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "measure_name": "PlaceholderMeasure",
            "format_string": "$#,##0.00"
        }
        
        result = await measure_operations.execute(OperationType.UPDATE, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "format_string" in data["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_measure_description(self, measure_operations, test_project_path):
        """Test updating a measure's description."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "measure_name": "PlaceholderMeasure",
            "description": "Updated description for the measure"
        }
        
        result = await measure_operations.execute(OperationType.UPDATE, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "description" in data["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_measure_multiple_fields(self, measure_operations, test_project_path):
        """Test updating multiple fields of a measure."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "measure_name": "PlaceholderMeasure",
            "expression": "SUM(Fact[Revenue]) + 1",
            "format_string": "#,##0",
            "description": "Multi-field update test"
        }
        
        result = await measure_operations.execute(OperationType.UPDATE, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert len(data["updated_fields"]) == 3
        assert all(field in data["updated_fields"] for field in ["expression", "format_string", "description"])

    @pytest.mark.asyncio
    async def test_update_measure_nonexistent(self, measure_operations, test_project_path):
        """Test updating a non-existent measure fails."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "measure_name": "NonExistent Measure",
            "expression": "SUM(Fact[Value])"
        }
        
        result = await measure_operations.execute(OperationType.UPDATE, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_measure_invalid_dax(self, measure_operations, test_project_path):
        """Test updating a measure with invalid DAX fails."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "measure_name": "PlaceholderMeasure",
            "expression": "SUM(Fact[Revenue)"  # Missing closing bracket
        }
        
        result = await measure_operations.execute(OperationType.UPDATE, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "invalid" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_delete_measure_success(self, measure_operations, test_project_path):
        """Test successfully deleting a measure."""
        # First add a measure to delete
        add_args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "measure_name": "Temp Measure",
            "expression": "SUM(Fact[Value])"
        }
        await measure_operations.execute(OperationType.ADD, add_args)
        
        # Now delete it
        delete_args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "measure_name": "Temp Measure"
        }
        
        result = await measure_operations.execute(OperationType.DELETE, delete_args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["table_name"] == "Fact"
        assert data["measure_name"] == "Temp Measure"
        assert data["action"] == "deleted"
        
        # Verify measure was actually deleted
        list_args = {"project_path": test_project_path, "table_name": "Fact"}
        list_result = await measure_operations.execute(OperationType.LIST, list_args)
        list_data = json.loads(list_result[0].text)
        
        measure_names = [m["name"] for m in list_data["measures"]]
        assert "Temp Measure" not in measure_names

    @pytest.mark.asyncio
    async def test_delete_measure_nonexistent(self, measure_operations, test_project_path):
        """Test deleting a non-existent measure fails."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "measure_name": "NonExistent Measure"
        }
        
        result = await measure_operations.execute(OperationType.DELETE, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_delete_measure_invalid_table(self, measure_operations, test_project_path):
        """Test deleting from a non-existent table fails."""
        args = {
            "project_path": test_project_path,
            "table_name": "NonExistentTable",
            "measure_name": "Some Measure"
        }
        
        result = await measure_operations.execute(OperationType.DELETE, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_unknown_operation(self, measure_operations, test_project_path):
        """Test that unknown operations return appropriate error."""
        result = await measure_operations.execute("unknown_operation", {"project_path": test_project_path})
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "unknown operation" in result[0].text.lower()