"""Tests for table operations."""

import pytest
import json

from pbip_mcp.operations import OperationType


class TestTableOperations:
    """Test cases for TableOperations."""

    @pytest.mark.asyncio
    async def test_list_tables(self, table_operations, test_project_path, expected_tables):
        """Test listing all tables in the project."""
        args = {"project_path": test_project_path}
        
        result = await table_operations.execute(OperationType.LIST, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert "tables" in data
        assert "count" in data
        assert data["count"] == len(expected_tables)
        
        # Verify table structure
        tables = data["tables"]
        assert all("name" in table for table in tables)
        assert all("column_count" in table for table in tables)
        assert all("measure_count" in table for table in tables)
        
        # Verify expected table names
        table_names = [table["name"] for table in tables]
        assert set(table_names) == set(expected_tables)

    @pytest.mark.asyncio
    async def test_list_tables_contains_fact_table(self, table_operations, test_project_path):
        """Test that the Fact table is included in the list with expected properties."""
        args = {"project_path": test_project_path}
        
        result = await table_operations.execute(OperationType.LIST, args)
        data = json.loads(result[0].text)
        
        fact_table = next((table for table in data["tables"] if table["name"] == "Fact"), None)
        assert fact_table is not None
        assert fact_table["column_count"] == 6  # Expected columns in Fact table
        assert fact_table["measure_count"] == 3  # Expected measures in Fact table

    @pytest.mark.asyncio
    async def test_get_table_details_fact(self, table_operations, test_project_path):
        """Test getting detailed information about the Fact table."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact"
        }
        
        result = await table_operations.execute(OperationType.GET, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["name"] == "Fact"
        assert "lineage_tag" in data
        assert "columns" in data
        assert "measures" in data
        assert "hierarchies" in data
        assert "partitions" in data
        
        # Verify columns details
        assert len(data["columns"]) == 6
        column_names = [col["name"] for col in data["columns"]]
        assert "Customer" in column_names
        assert "Product" in column_names
        assert "Revenue" in column_names
        assert "Date" in column_names
        
        # Verify measures details
        assert len(data["measures"]) == 3
        measure_names = [measure["name"] for measure in data["measures"]]
        assert "PlaceholderMeasure" in measure_names
        assert "Total Revenue" in measure_names
        assert "Transaction Count" in measure_names

    @pytest.mark.asyncio
    async def test_get_table_details_includes_column_properties(self, table_operations, test_project_path):
        """Test that table details include comprehensive column properties."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact"
        }
        
        result = await table_operations.execute(OperationType.GET, args)
        data = json.loads(result[0].text)
        
        # Check that columns have expected properties
        for column in data["columns"]:
            assert "name" in column
            assert "data_type" in column
            assert "lineage_tag" in column
            assert "summarize_by" in column
            assert "is_hidden" in column

    @pytest.mark.asyncio
    async def test_get_table_details_includes_measure_properties(self, table_operations, test_project_path):
        """Test that table details include comprehensive measure properties."""
        args = {
            "project_path": test_project_path,
            "table_name": "Fact"
        }
        
        result = await table_operations.execute(OperationType.GET, args)
        data = json.loads(result[0].text)
        
        # Check that measures have expected properties
        for measure in data["measures"]:
            assert "name" in measure
            assert "expression" in measure
            assert "lineage_tag" in measure
            assert "is_hidden" in measure

    @pytest.mark.asyncio
    async def test_get_table_details_nonexistent_table(self, table_operations, test_project_path):
        """Test getting details for a non-existent table fails."""
        args = {
            "project_path": test_project_path,
            "table_name": "NonExistentTable"
        }
        
        result = await table_operations.execute(OperationType.GET, args)
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "not found" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_get_table_details_metricname_table(self, table_operations, test_project_path):
        """Test getting details for the MetricName table."""
        args = {
            "project_path": test_project_path,
            "table_name": "MetricName"
        }
        
        result = await table_operations.execute(OperationType.GET, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["name"] == "MetricName"
        assert "columns" in data
        assert len(data["columns"]) >= 1  # Should have at least one column

    @pytest.mark.asyncio
    async def test_get_table_details_month_table(self, table_operations, test_project_path):
        """Test getting details for the Month table."""
        args = {
            "project_path": test_project_path,
            "table_name": "Month"
        }
        
        result = await table_operations.execute(OperationType.GET, args)
        assert len(result) == 1
        
        data = json.loads(result[0].text)
        assert data["name"] == "Month"
        assert "columns" in data
        assert len(data["columns"]) >= 1  # Should have at least one column

    @pytest.mark.asyncio
    async def test_list_tables_invalid_project_path(self, table_operations):
        """Test listing tables with invalid project path fails."""
        args = {"project_path": "/nonexistent/path"}
        
        result = await table_operations.execute(OperationType.LIST, args)
        assert len(result) == 1
        assert "Error:" in result[0].text

    @pytest.mark.asyncio
    async def test_get_table_details_invalid_project_path(self, table_operations):
        """Test getting table details with invalid project path fails."""
        args = {
            "project_path": "/nonexistent/path",
            "table_name": "SomeTable"
        }
        
        result = await table_operations.execute(OperationType.GET, args)
        assert len(result) == 1
        assert "Error:" in result[0].text

    @pytest.mark.asyncio
    async def test_table_lineage_tags_exist(self, table_operations, test_project_path):
        """Test that tables have valid lineage tags."""
        args = {"project_path": test_project_path}
        
        result = await table_operations.execute(OperationType.LIST, args)
        data = json.loads(result[0].text)
        
        for table in data["tables"]:
            assert "lineage_tag" in table
            assert table["lineage_tag"] is not None
            assert len(table["lineage_tag"]) > 0

    @pytest.mark.asyncio
    async def test_unknown_operation(self, table_operations, test_project_path):
        """Test that unknown operations return appropriate error."""
        result = await table_operations.execute("unknown_operation", {"project_path": test_project_path})
        assert len(result) == 1
        assert "Error:" in result[0].text
        assert "unknown operation" in result[0].text.lower()