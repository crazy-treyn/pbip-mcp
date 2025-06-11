"""Tests for the MCP server functionality."""

import pytest
import json
from pathlib import Path

from pbip_mcp.server import SimplifiedPBIPServer


class TestSimplifiedPBIPServer:
    """Test cases for SimplifiedPBIPServer."""

    @pytest.fixture
    def server(self):
        """Create a SimplifiedPBIPServer instance for testing."""
        return SimplifiedPBIPServer()

    @pytest.mark.asyncio
    async def test_list_projects_finds_both_types(self, server, temp_dir):
        """Test that list_projects finds both PBIP projects and standalone semantic models."""
        # Set up test directory with both types
        test_dir = temp_dir / "mixed_projects"
        test_dir.mkdir()
        
        # Copy fixtures
        fixtures_dir = Path(__file__).parent / "fixtures"
        
        # PBIP project
        pbip_dir = test_dir / "pbip_project"
        pbip_dir.mkdir()
        shutil.copy2(fixtures_dir / "pbip_project" / "TestCalcGroups.pbip", pbip_dir)
        shutil.copytree(fixtures_dir / "pbip_project" / "TestCalcGroups.SemanticModel", 
                       pbip_dir / "TestCalcGroups.SemanticModel")
        
        # Standalone semantic model
        shutil.copytree(fixtures_dir / "standalone_semantic_model" / "TestCalcGroups.SemanticModel",
                       test_dir / "Standalone.SemanticModel")
        
        args = {"directory": str(test_dir)}
        result = await server._list_projects(args)
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        
        assert data["count"] == 2
        projects = data["projects"]
        
        # Should find both types
        types = [p["type"] for p in projects]
        assert "pbip_project" in types
        assert "standalone_semantic_model" in types

    @pytest.mark.asyncio
    async def test_list_projects_standalone_only(self, server, standalone_semantic_model_path):
        """Test list_projects with only standalone semantic models."""
        args = {"directory": str(standalone_semantic_model_path.parent)}
        result = await server._list_projects(args)
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        
        assert data["count"] == 1
        project = data["projects"][0]
        assert project["type"] == "standalone_semantic_model"
        assert project["name"] == "TestCalcGroups"
        assert project["has_semantic_model"] is True
        assert project["has_report"] is False

    @pytest.mark.asyncio
    async def test_list_projects_pbip_only(self, server, pbip_project_path):
        """Test list_projects with only PBIP projects."""
        args = {"directory": str(pbip_project_path.parent)}
        result = await server._list_projects(args)
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        
        assert data["count"] == 1
        project = data["projects"][0]
        assert project["type"] == "pbip_project"
        assert project["name"] == "TestCalcGroups"
        assert project["has_semantic_model"] is True

    @pytest.mark.asyncio
    async def test_list_projects_nonexistent_directory(self, server):
        """Test list_projects with non-existent directory."""
        args = {"directory": "/nonexistent/path"}
        result = await server._list_projects(args)
        
        assert len(result) == 1
        assert "Directory not found" in result[0].text

    @pytest.mark.asyncio
    async def test_load_project_standalone_semantic_model(self, server, standalone_semantic_model_path):
        """Test loading a standalone semantic model project."""
        args = {"project_path": str(standalone_semantic_model_path)}
        result = await server._load_project(args)
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        
        assert "project_info" in data
        assert "semantic_model" in data
        assert data["project_info"]["has_semantic_model"] is True
        assert data["semantic_model"]["name"] == "Model"
        assert data["semantic_model"]["table_count"] == 5

    @pytest.mark.asyncio
    async def test_load_project_pbip_project(self, server, pbip_project_path):
        """Test loading a complete PBIP project."""
        args = {"project_path": str(pbip_project_path)}
        result = await server._load_project(args)
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        
        assert "project_info" in data
        assert "semantic_model" in data
        assert data["project_info"]["has_semantic_model"] is True
        assert data["semantic_model"]["name"] == "Model"
        assert data["semantic_model"]["table_count"] == 5

    @pytest.mark.asyncio
    async def test_load_project_nonexistent_path(self, server):
        """Test loading project with non-existent path."""
        args = {"project_path": "/nonexistent/path"}
        result = await server._load_project(args)
        
        assert len(result) == 1
        assert "Error loading project" in result[0].text

    def test_tool_registry_contains_all_operations(self, server):
        """Test that the tool registry contains all expected operations."""
        expected_tools = [
            "list_measures", "add_measure", "update_measure", "delete_measure",
            "list_columns", "add_column", "update_column", "delete_column", 
            "list_tables", "get_table_details",
            "list_relationships",
            "list_projects", "load_project"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in server.tools

    def test_tool_descriptions_mention_both_types(self, server):
        """Test that tool descriptions mention both .pbip and .SemanticModel support."""
        project_path_tools = [
            "list_measures", "add_measure", "update_measure", "delete_measure",
            "list_columns", "add_column", "update_column", "delete_column",
            "list_tables", "get_table_details", "list_relationships"
        ]
        
        for tool_name in project_path_tools:
            tool = server.tools[tool_name]["tool"]
            project_path_desc = tool.inputSchema["properties"]["project_path"]["description"]
            assert ".SemanticModel" in project_path_desc
            assert ".pbip" in project_path_desc or "PBIP" in project_path_desc

    def test_list_projects_tool_description(self, server):
        """Test that list_projects tool description mentions both types."""
        tool = server.tools["list_projects"]["tool"]
        assert ".SemanticModel" in tool.description
        directory_desc = tool.inputSchema["properties"]["directory"]["description"]
        assert ".SemanticModel" in directory_desc

    def test_load_project_tool_description(self, server):
        """Test that load_project tool description mentions both types."""
        tool = server.tools["load_project"]["tool"]
        assert "semantic model" in tool.description.lower()
        project_path_desc = tool.inputSchema["properties"]["project_path"]["description"]
        assert ".SemanticModel" in project_path_desc

    @pytest.mark.asyncio
    async def test_measure_operations_integration(self, server, test_project_path):
        """Test measure operations through the server interface."""
        # Test list measures
        result = await server.tools["list_measures"]["handler"]({
            "project_path": test_project_path
        })
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "measures" in data

    @pytest.mark.asyncio
    async def test_column_operations_integration(self, server, test_project_path):
        """Test column operations through the server interface."""
        # Test list columns
        result = await server.tools["list_columns"]["handler"]({
            "project_path": test_project_path,
            "table_name": "Fact"
        })
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "columns" in data

    @pytest.mark.asyncio
    async def test_table_operations_integration(self, server, test_project_path):
        """Test table operations through the server interface."""
        # Test list tables
        result = await server.tools["list_tables"]["handler"]({
            "project_path": test_project_path
        })
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "tables" in data

    @pytest.mark.asyncio
    async def test_relationship_operations_integration(self, server, test_project_path):
        """Test relationship operations through the server interface."""
        # Test list relationships
        result = await server.tools["list_relationships"]["handler"]({
            "project_path": test_project_path
        })
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "relationships" in data

    def test_server_initialization(self, server):
        """Test that server initializes correctly."""
        assert server.app is not None
        assert server.project_parser is not None
        assert server.tmdl_writer is not None
        assert len(server.operations) == 4  # measure, column, table, relationship
        assert len(server.tools) > 0

    def test_operation_handler_registration(self, server):
        """Test that operation handlers are registered correctly."""
        assert "measure" in server.operations
        assert "column" in server.operations
        assert "table" in server.operations
        assert "relationship" in server.operations

    def test_help_text_generation(self, server):
        """Test that help text is generated correctly."""
        help_text = server._get_help_text()
        assert "PBIP MCP Server Help" in help_text
        assert "semantic model" in help_text.lower()
        assert "Table Operations" in help_text
        assert "Measure Operations" in help_text

    def test_tmdl_syntax_guide(self, server):
        """Test that TMDL syntax guide is available."""
        guide = server._get_tmdl_syntax_guide()
        assert "TMDL Syntax Guide" in guide
        assert "measure" in guide.lower()
        assert "column" in guide.lower()
        assert "table" in guide.lower()


# Import shutil for copying files in tests
import shutil