"""Table operations for PBIP MCP Server."""

from typing import Any, Dict, List

from mcp.types import TextContent

from .base import BaseOperation, OperationType


class TableOperations(BaseOperation):
    """Handle table-level operations."""
    
    async def execute(self, operation: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the specified table operation."""
        if operation == OperationType.LIST:
            return await self.list_tables(arguments)
        elif operation == OperationType.GET:
            return await self.get_table_details(arguments)
        else:
            return self._error_response(f"Unknown operation: {operation}")
    
    async def list_tables(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List all tables in the project."""
        project = self._load_project(arguments["project_path"])
        
        tables = []
        for table in project.semantic_model.tables:
            tables.append({
                "name": table.name,
                "column_count": len(table.columns),
                "measure_count": len(table.measures),
                "partition_count": len(table.partitions),
                "hierarchy_count": len(table.hierarchies),
                "is_hidden": table.is_hidden,
                "is_private": table.is_private,
                "lineage_tag": table.lineage_tag
            })
        
        return self._success_response({
            "count": len(tables),
            "tables": tables
        })
    
    async def get_table_details(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get detailed information about a table."""
        project = self._load_project(arguments["project_path"])
        table_name = arguments["table_name"]
        
        # Find table using normalized name comparison
        normalized_input_name = self._normalize_element_name(table_name)
        table = next((t for t in project.semantic_model.tables if self._normalize_element_name(t.name) == normalized_input_name), None)
        if not table:
            return self._error_response(f"Table '{table_name}' not found")
        
        result = {
            "name": table.name,
            "lineage_tag": table.lineage_tag,
            "is_hidden": table.is_hidden,
            "is_private": table.is_private,
            "columns": [
                {
                    "name": c.name,
                    "data_type": c.data_type,
                    "summarize_by": c.summarize_by,
                    "is_calculated": c.expression is not None
                } for c in table.columns
            ],
            "measures": [
                {
                    "name": m.name,
                    "expression": m.expression[:100] + "..." if len(m.expression) > 100 else m.expression,
                    "format_string": m.format_string
                } for m in table.measures
            ],
            "partitions": [
                {
                    "name": p.name,
                    "mode": p.mode,
                    "source_type": "M Query" if p.source.strip().startswith("let") else "DAX"
                } for p in table.partitions
            ],
            "hierarchies": [
                {
                    "name": h.name,
                    "levels": [{"name": l.name, "column": l.column} for l in h.levels]
                } for h in table.hierarchies
            ]
        }
        
        # Add relationships involving this table
        relationships_from = []
        relationships_to = []
        
        for rel in project.semantic_model.relationships:
            if rel.from_table == table_name:
                relationships_from.append({
                    "to": f"{rel.to_table}[{rel.to_column}]",
                    "cardinality": rel.cardinality,
                    "is_active": rel.is_active
                })
            elif rel.to_table == table_name:
                relationships_to.append({
                    "from": f"{rel.from_table}[{rel.from_column}]",
                    "cardinality": rel.cardinality,
                    "is_active": rel.is_active
                })
        
        result["relationships"] = {
            "from_this_table": relationships_from,
            "to_this_table": relationships_to
        }
        
        return self._success_response(result)