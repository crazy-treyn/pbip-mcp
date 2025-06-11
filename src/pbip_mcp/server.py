"""Simplified and extensible PBIP MCP Server."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Type

from mcp.server import Server
from mcp.types import Resource, TextContent, Tool

from .parsers import ProjectParser
from .writers import TMDLWriter
from .operations import (
    BaseOperation,
    OperationType,
    MeasureOperations,
    ColumnOperations,
    TableOperations,
    RelationshipOperations,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimplifiedPBIPServer:
    """Simplified PBIP MCP Server with clean, extensible architecture."""
    
    def __init__(self):
        self.app = Server("pbip-mcp-server")
        
        # Shared dependencies
        self.project_parser = ProjectParser()
        self.tmdl_writer = TMDLWriter()
        
        # Initialize operation handlers
        self.operations = {
            "measure": MeasureOperations(self.project_parser, self.tmdl_writer),
            "column": ColumnOperations(self.project_parser, self.tmdl_writer),
            "table": TableOperations(self.project_parser, self.tmdl_writer),
            "relationship": RelationshipOperations(self.project_parser, self.tmdl_writer),
        }
        
        # Build tool registry
        self.tools = self._build_tool_registry()
        
        # Register MCP handlers
        self._register_handlers()
    
    def register_operation_handler(self, name: str, handler_class: Type[BaseOperation]):
        """Register a new operation handler - makes it easy to extend."""
        self.operations[name] = handler_class(self.project_parser, self.tmdl_writer)
        # Rebuild tool registry to include new operations
        self.tools = self._build_tool_registry()
    
    def _build_tool_registry(self) -> Dict[str, Dict[str, Any]]:
        """Build tool registry from registered operations."""
        tools = {}
        
        # Measure tools
        tools.update({
            "list_measures": {
                "handler": lambda args: self.operations["measure"].execute(OperationType.LIST, args),
                "tool": Tool(
                    name="list_measures",
                    description="List all measures in the project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to PBIP project file or .SemanticModel directory"},
                            "table_name": {"type": "string", "description": "Filter by table name (optional)"}
                        },
                        "required": ["project_path"]
                    }
                )
            },
            "add_measure": {
                "handler": lambda args: self.operations["measure"].execute(OperationType.ADD, args),
                "tool": Tool(
                    name="add_measure",
                    description="Add a new measure to a table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to PBIP project file or .SemanticModel directory"},
                            "table_name": {"type": "string", "description": "Table to add measure to"},
                            "measure_name": {"type": "string", "description": "Name of the new measure"},
                            "expression": {"type": "string", "description": "DAX expression"},
                            "description": {"type": "string", "description": "Measure description (optional)"},
                            "format_string": {"type": "string", "description": "Format string (optional)"}
                        },
                        "required": ["project_path", "table_name", "measure_name", "expression"]
                    }
                )
            },
            "update_measure": {
                "handler": lambda args: self.operations["measure"].execute(OperationType.UPDATE, args),
                "tool": Tool(
                    name="update_measure",
                    description="Update an existing measure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to PBIP project file or .SemanticModel directory"},
                            "table_name": {"type": "string", "description": "Table containing the measure"},
                            "measure_name": {"type": "string", "description": "Name of the measure to update"},
                            "expression": {"type": "string", "description": "New DAX expression (optional)"},
                            "description": {"type": "string", "description": "New description (optional)"},
                            "format_string": {"type": "string", "description": "New format string (optional)"}
                        },
                        "required": ["project_path", "table_name", "measure_name"]
                    }
                )
            },
            "delete_measure": {
                "handler": lambda args: self.operations["measure"].execute(OperationType.DELETE, args),
                "tool": Tool(
                    name="delete_measure",
                    description="Delete a measure from a table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to PBIP project file or .SemanticModel directory"},
                            "table_name": {"type": "string", "description": "Table containing the measure"},
                            "measure_name": {"type": "string", "description": "Name of the measure to delete"}
                        },
                        "required": ["project_path", "table_name", "measure_name"]
                    }
                )
            },
        })
        
        # Column tools
        tools.update({
            "list_columns": {
                "handler": lambda args: self.operations["column"].execute(OperationType.LIST, args),
                "tool": Tool(
                    name="list_columns",
                    description="List all columns in a table or all tables (if table_name omitted)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to PBIP project file or .SemanticModel directory"},
                            "table_name": {"type": "string", "description": "Table name (optional - omit to get all columns from all tables)"}
                        },
                        "required": ["project_path"]
                    }
                )
            },
            "add_column": {
                "handler": lambda args: self.operations["column"].execute(OperationType.ADD, args),
                "tool": Tool(
                    name="add_column",
                    description="Add a new column to a table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to PBIP project file or .SemanticModel directory"},
                            "table_name": {"type": "string", "description": "Table to add column to"},
                            "column_name": {"type": "string", "description": "Name of the new column"},
                            "data_type": {"type": "string", "description": "Data type (string, int64, double, boolean, dateTime)", "default": "string"},
                            "expression": {"type": "string", "description": "DAX expression for calculated column (optional)"},
                            "format_string": {"type": "string", "description": "Format string (optional)"},
                            "summarize_by": {"type": "string", "description": "Summarization type (none, sum, count, min, max, average)"},
                            "is_hidden": {"type": "boolean", "description": "Hide column (optional)", "default": False}
                        },
                        "required": ["project_path", "table_name", "column_name"]
                    }
                )
            },
            "update_column": {
                "handler": lambda args: self.operations["column"].execute(OperationType.UPDATE, args),
                "tool": Tool(
                    name="update_column",
                    description="Update an existing column",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to PBIP project file or .SemanticModel directory"},
                            "table_name": {"type": "string", "description": "Table containing the column"},
                            "column_name": {"type": "string", "description": "Name of the column to update"},
                            "data_type": {"type": "string", "description": "New data type (optional)"},
                            "expression": {"type": "string", "description": "New DAX expression for calculated column (optional)"},
                            "format_string": {"type": "string", "description": "New format string (optional)"},
                            "summarize_by": {"type": "string", "description": "New summarization type (optional)"},
                            "is_hidden": {"type": "boolean", "description": "Hide/show column (optional)"}
                        },
                        "required": ["project_path", "table_name", "column_name"]
                    }
                )
            },
            "delete_column": {
                "handler": lambda args: self.operations["column"].execute(OperationType.DELETE, args),
                "tool": Tool(
                    name="delete_column",
                    description="Delete a column from a table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to PBIP project file or .SemanticModel directory"},
                            "table_name": {"type": "string", "description": "Table containing the column"},
                            "column_name": {"type": "string", "description": "Name of the column to delete"}
                        },
                        "required": ["project_path", "table_name", "column_name"]
                    }
                )
            },
        })
        
        # Table tools
        tools.update({
            "list_tables": {
                "handler": lambda args: self.operations["table"].execute(OperationType.LIST, args),
                "tool": Tool(
                    name="list_tables",
                    description="List all tables in the project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to PBIP project file or .SemanticModel directory"}
                        },
                        "required": ["project_path"]
                    }
                )
            },
            "get_table_details": {
                "handler": lambda args: self.operations["table"].execute(OperationType.GET, args),
                "tool": Tool(
                    name="get_table_details",
                    description="Get detailed information about a table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to PBIP project file or .SemanticModel directory"},
                            "table_name": {"type": "string", "description": "Table name"}
                        },
                        "required": ["project_path", "table_name"]
                    }
                )
            },
            "get_model_details": {
                "handler": lambda args: self.operations["table"].execute(OperationType.GET_MODEL_DETAILS, args),
                "tool": Tool(
                    name="get_model_details",
                    description="Get comprehensive details of the entire semantic model with all tables, columns, measures, and relationships",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to PBIP project file or .SemanticModel directory"}
                        },
                        "required": ["project_path"]
                    }
                )
            },
        })
        
        # Relationship tools
        tools.update({
            "list_relationships": {
                "handler": lambda args: self.operations["relationship"].execute(OperationType.LIST, args),
                "tool": Tool(
                    name="list_relationships",
                    description="List all relationships in the project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to PBIP project file or .SemanticModel directory"}
                        },
                        "required": ["project_path"]
                    }
                )
            },
        })
        
        # Project-level tools
        tools.update({
            "list_projects": {
                "handler": self._list_projects,
                "tool": Tool(
                    name="list_projects",
                    description="List all PBIP projects and standalone semantic models in a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory": {"type": "string", "description": "Directory path to scan for PBIP projects and standalone .SemanticModel directories"}
                        },
                        "required": ["directory"]
                    }
                )
            },
            "load_project": {
                "handler": self._load_project,
                "tool": Tool(
                    name="load_project",
                    description="Load complete project structure and metadata from PBIP project or standalone semantic model",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {"type": "string", "description": "Path to PBIP project file, directory, or .SemanticModel directory"}
                        },
                        "required": ["project_path"]
                    }
                )
            },
        })
        
        return tools
    
    def _register_handlers(self):
        """Register MCP protocol handlers."""
        
        @self.app.list_tools()
        async def list_tools():
            """List all available tools."""
            return [tool_info["tool"] for tool_info in self.tools.values()]
        
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            if name not in self.tools:
                return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
            
            try:
                handler = self.tools[name]["handler"]
                return await handler(arguments)
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}", exc_info=True)
                # Ensure error response is valid JSON
                error_response = {
                    "error": str(e),
                    "tool": name,
                    "type": type(e).__name__
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]
        
        @self.app.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources."""
            return [
                Resource(
                    uri="pbip://help",
                    name="PBIP MCP Server Help",
                    description="Help and usage information for the PBIP MCP Server"
                ),
                Resource(
                    uri="pbip://tmdl/syntax",
                    name="TMDL Syntax Guide",
                    description="Guide to Tabular Model Definition Language syntax"
                ),
            ]
        
        @self.app.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content."""
            if uri == "pbip://help":
                return self._get_help_text()
            elif uri == "pbip://tmdl/syntax":
                return self._get_tmdl_syntax_guide()
            return f"Unknown resource: {uri}"
    
    async def _list_projects(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List PBIP projects and standalone semantic models in a directory."""
        import json
        from pathlib import Path
        
        directory = Path(arguments["directory"])
        if not directory.exists():
            return [TextContent(type="text", text=f"Directory not found: {directory}")]
        
        projects = []
        processed_dirs = set()
        
        # Find .pbip projects
        for pbip_file in directory.rglob("*.pbip"):
            try:
                project_info = {
                    "name": pbip_file.stem,
                    "path": str(pbip_file),
                    "directory": str(pbip_file.parent),
                    "type": "pbip_project",
                    "has_semantic_model": any(pbip_file.parent.glob("*.SemanticModel")),
                    "has_report": any(pbip_file.parent.glob("*.Report"))
                }
                projects.append(project_info)
                processed_dirs.add(pbip_file.parent)
            except Exception as e:
                logger.warning(f"Error scanning project {pbip_file}: {e}")
        
        # Find standalone .SemanticModel directories
        for semantic_dir in directory.rglob("*.SemanticModel"):
            try:
                # Skip if this semantic model is already part of a .pbip project
                if semantic_dir.parent in processed_dirs:
                    continue
                    
                project_info = {
                    "name": semantic_dir.name.replace('.SemanticModel', ''),
                    "path": str(semantic_dir),
                    "directory": str(semantic_dir.parent),
                    "type": "standalone_semantic_model",
                    "has_semantic_model": True,
                    "has_report": False
                }
                projects.append(project_info)
            except Exception as e:
                logger.warning(f"Error scanning semantic model {semantic_dir}: {e}")
        
        return [TextContent(type="text", text=json.dumps({
            "count": len(projects),
            "projects": projects
        }, indent=2))]
    
    async def _load_project(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Load complete project structure."""
        import json
        
        try:
            project = self.project_parser.load_project(arguments["project_path"])
            
            result = {
                "project_info": {
                    "version": project.project_info.version,
                    "artifacts": len(project.project_info.artifacts),
                    "has_semantic_model": project.semantic_model is not None,
                },
                "semantic_model": None
            }
            
            if project.semantic_model:
                result["semantic_model"] = {
                    "name": project.semantic_model.name,
                    "culture": project.semantic_model.culture,
                    "table_count": len(project.semantic_model.tables),
                    "relationship_count": len(project.semantic_model.relationships),
                    "total_measures": sum(len(t.measures) for t in project.semantic_model.tables),
                    "total_columns": sum(len(t.columns) for t in project.semantic_model.tables),
                }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error loading project: {str(e)}")]
    
    def _get_help_text(self) -> str:
        """Get help text for the server."""
        tool_categories = {
            "Project Management": ["list_projects", "load_project"],
            "Table Operations": ["list_tables", "get_table_details"],
            "Column Operations": ["list_columns", "add_column", "update_column", "delete_column"],
            "Measure Operations": ["list_measures", "add_measure", "update_measure", "delete_measure"],
            "Relationship Operations": ["list_relationships"],
        }
        
        help_text = """# PBIP MCP Server Help

A simplified and extensible MCP server for Power BI Desktop Project (.pbip) files.

## Features:
- Clean, modular architecture that's easy to extend
- Comprehensive support for measures, columns, tables, and relationships
- Consistent error handling and response formats
- TMDL syntax preservation and validation

## Available Tools by Category:

"""
        
        for category, tool_names in tool_categories.items():
            help_text += f"### {category}\n"
            for tool_name in tool_names:
                if tool_name in self.tools:
                    tool = self.tools[tool_name]["tool"]
                    help_text += f"- **{tool_name}**: {tool.description}\n"
            help_text += "\n"
        
        help_text += """## Extending the Server:

To add new operations:

1. Create a new operation class inheriting from `BaseOperation`
2. Implement the `execute` method with your operation logic
3. Register the operation handler with the server
4. Add corresponding tools to the tool registry

Example:
```python
class MyCustomOperations(BaseOperation):
    async def execute(self, operation: str, arguments: Dict[str, Any]) -> List[TextContent]:
        # Your custom logic here
        pass

# Register the handler
server.register_operation_handler("custom", MyCustomOperations)
```

## Error Handling:
All errors are returned in a consistent format with descriptive messages.
The server validates inputs and provides helpful error messages when operations fail.
"""
        
        return help_text
    
    def _get_tmdl_syntax_guide(self) -> str:
        """Get TMDL syntax guide."""
        return """# TMDL Syntax Guide

Tabular Model Definition Language (TMDL) uses indentation-based syntax similar to YAML.

## Basic Structure:
```
model ModelName
    culture: en-US
    
    table TableName
        lineageTag: unique-id
        
        column ColumnName
            dataType: string
            lineageTag: unique-id
            
        measure MeasureName = DAX_Expression
            lineageTag: unique-id
            formatString: "0.00"
```

## Key Elements:

### Tables
Define data structures and contain columns, measures, and hierarchies.
```
table Sales
    lineageTag: 4f8e6d3a-1234-5678-90ab-cdef12345678
    
    column ProductID
        dataType: int64
        lineageTag: a1b2c3d4-5678-90ab-cdef-123456789012
```

### Columns
Define data fields with types and properties.
```
column Amount
    dataType: double
    lineageTag: unique-id
    formatString: "$#,##0.00"
    summarizeBy: sum
```

### Calculated Columns
Use DAX expressions to compute values.
```
column YearMonth = FORMAT([Date], "YYYY-MM")
    dataType: string
    lineageTag: unique-id
```

### Measures
Define DAX calculations for aggregations.
```
/// Total sales amount for the period
measure Total Sales = SUM(Sales[Amount])
    lineageTag: unique-id
    formatString: "$#,##0.00"
```

### Relationships
Define connections between tables.
```
relationship rel_Sales_Product
    fromColumn: Sales.ProductID
    toColumn: Product.ProductID
    cardinality: ManyToOne
    isActive: true
```

## Comments:
- Use `/// Description` above measures for business descriptions
- Use `//` for regular code comments

## Data Types:
- string
- int64
- double
- boolean
- dateTime
- binary

## Summarization Types:
- none
- sum
- count
- min
- max
- average

## Best Practices:
1. Always include lineageTag for tracking
2. Use descriptive names for measures and columns
3. Add business descriptions for measures using /// comments
4. Format DAX expressions for readability
5. Group related measures together
"""
    
    async def run_stdio(self):
        """Run server with stdio transport."""
        import mcp.server.stdio
        
        logger.info("Starting Simplified PBIP MCP Server")
        
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream, write_stream, self.app.create_initialization_options()
            )


def main():
    """Main entry point."""
    server = SimplifiedPBIPServer()
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()