"""Tests for column operations."""

import pytest
import json

from pbip_mcp.operations import OperationType


class TestColumnOperations:
    """Test cases for ColumnOperations."""

    @pytest.mark.asyncio
    async def test_list_columns(self, column_operations, test_project_path):
        """Test listing columns for a specific table."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact"
        }
        
        result = await column_operations.execute(OperationType.LIST, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert "columns" in data
        assert "count" in data
        assert data["count"] == 6  # Expected number of columns in Fact table
        
        # Verify column structure
        columns = data["columns"]
        assert all("name" in column for column in columns)
        assert all("data_type" in column for column in columns)
        assert all("lineage_tag" in column for column in columns)

    @pytest.mark.asyncio
    async def test_list_columns_specific_names(self, column_operations, test_project_path, expected_fact_columns):
        """Test that listed columns match expected column names."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact"
        }
        
        result = await column_operations.execute(OperationType.LIST, args)
        data = json.loads(result[0].text)
        
        column_names = [col["name"] for col in data["columns"]]
        assert set(column_names) == set(expected_fact_columns)

    @pytest.mark.asyncio
    async def test_list_columns_invalid_table(self, column_operations, test_project_path):
        """Test listing columns for non-existent table fails."""
        args = {
            "project_path": test_project_path,
            "table_name": "NonExistentTable"
        }
        
        result = await column_operations.execute(OperationType.LIST, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_add_column_success(self, column_operations, test_project_path, sample_column_args):
        """Test successfully adding a new column."""
        args = {**sample_column_args, "project_path": test_project_path}
        
        result = await column_operations.execute(OperationType.ADD, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["table_name"] == "Fact"
        assert data["column_name"] == "Test Column"
        assert data["action"] == "added"
        
        # Verify column was actually added
        list_args = {"project_path": test_project_path, "table_name": "Fact"}
        list_result = await column_operations.execute(OperationType.LIST, list_args)
        list_data = json.loads(list_result[0].text)
        
        column_names = [c["name"] for c in list_data["columns"]]
        assert "Test Column" in column_names

    @pytest.mark.asyncio
    async def test_add_column_with_expression(self, column_operations, test_project_path):
        """Test adding a calculated column with DAX expression."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "column_name": "Calculated Column",
            "data_type": "string",
            "expression": "LEFT(Fact[MetricName], 5)"
        }
        
        result = await column_operations.execute(OperationType.ADD, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_add_column_duplicate_name(self, column_operations, test_project_path):
        """Test adding a column with duplicate name fails."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "column_name": "Customer",  # Already exists
            "data_type": "string"
        }
        
        result = await column_operations.execute(OperationType.ADD, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "already exists" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_add_column_invalid_table(self, column_operations, test_project_path, sample_column_args):
        """Test adding column to non-existent table fails."""
        args = {**sample_column_args, "project_path": test_project_path, "table_name": "NonExistentTable"}
        
        result = await column_operations.execute(OperationType.ADD, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_update_column_data_type(self, column_operations, test_project_path):
        """Test updating a column's data type."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "column_name": "Customer",
            "data_type": "string"
        }
        
        result = await column_operations.execute(OperationType.UPDATE, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["table_name"] == "Fact"
        assert data["column_name"] == "Customer"
        assert "data_type" in data["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_column_format_string(self, column_operations, test_project_path):
        """Test updating a column's format string."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "column_name": "Revenue",
            "format_string": "#,##0.00"
        }
        
        result = await column_operations.execute(OperationType.UPDATE, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "format_string" in data["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_column_summarize_by(self, column_operations, test_project_path):
        """Test updating a column's summarization type."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "column_name": "Revenue",
            "summarize_by": "sum"
        }
        
        result = await column_operations.execute(OperationType.UPDATE, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "summarize_by" in data["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_column_is_hidden(self, column_operations, test_project_path):
        """Test updating a column's hidden status."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "column_name": "Revenue",
            "is_hidden": True
        }
        
        result = await column_operations.execute(OperationType.UPDATE, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "is_hidden" in data["updated_fields"]

    @pytest.mark.asyncio
    async def test_update_column_multiple_fields(self, column_operations, test_project_path):
        """Test updating multiple fields of a column."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "column_name": "Revenue",
            "data_type": "double",
            "format_string": "#,##0",
            "summarize_by": "average"
        }
        
        result = await column_operations.execute(OperationType.UPDATE, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert len(data["updated_fields"]) == 3
        assert all(field in data["updated_fields"] for field in ["data_type", "format_string", "summarize_by"])

    @pytest.mark.asyncio
    async def test_update_column_nonexistent(self, column_operations, test_project_path):
        """Test updating a non-existent column fails."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "column_name": "NonExistent Column",
            "data_type": "string"
        }
        
        result = await column_operations.execute(OperationType.UPDATE, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_delete_column_success(self, column_operations, test_project_path):
        """Test successfully deleting a column."""
        # First add a column to delete
        add_args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "column_name": "Temp Column",
            "data_type": "string"
        }
        await column_operations.execute(OperationType.ADD, add_args)
        
        # Now delete it
        delete_args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "column_name": "Temp Column"
        }
        
        result = await column_operations.execute(OperationType.DELETE, delete_args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["table_name"] == "Fact"
        assert data["column_name"] == "Temp Column"
        assert data["action"] == "deleted"
        
        # Verify column was actually deleted
        list_args = {"project_path": test_project_path, "table_name": "Fact"}
        list_result = await column_operations.execute(OperationType.LIST, list_args)
        list_data = json.loads(list_result[0].text)
        
        column_names = [c["name"] for c in list_data["columns"]]
        assert "Temp Column" not in column_names

    @pytest.mark.asyncio
    async def test_delete_column_nonexistent(self, column_operations, test_project_path):
        """Test deleting a non-existent column fails."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact",
            "column_name": "NonExistent Column"
        }
        
        result = await column_operations.execute(OperationType.DELETE, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_delete_column_invalid_table(self, column_operations, test_project_path):
        """Test deleting from a non-existent table fails."""
        args = {
            "project_path": test_project_path,
            "table_name": "NonExistentTable",
            "column_name": "Some Column"
        }
        
        result = await column_operations.execute(OperationType.DELETE, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_unknown_operation(self, column_operations, test_project_path):
        """Test that unknown operations return appropriate error."""
        result = await column_operations.execute("unknown_operation", {"project_path": test_project_path})
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "unknown operation" in result[0].text.lower()