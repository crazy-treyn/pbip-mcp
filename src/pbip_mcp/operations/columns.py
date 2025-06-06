"""Column operations for PBIP MCP Server."""

from typing import Any, Dict, List

from mcp.types import TextContent

from .base import BaseOperation, OperationType


class ColumnOperations(BaseOperation):
    """Handle all column-related operations."""
    
    async def execute(self, operation: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the specified column operation."""
        if operation == OperationType.LIST:
            return await self.list_columns(arguments)
        elif operation == OperationType.ADD:
            return await self.add_column(arguments)
        elif operation == OperationType.UPDATE:
            return await self.update_column(arguments)
        elif operation == OperationType.DELETE:
            return await self.delete_column(arguments)
        else:
            return self._error_response(f"Unknown operation: {operation}")
    
    async def list_columns(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List all columns in a table."""
        project = self._load_project(arguments["project_path"])
        table_name = arguments["table_name"]
        
        table = next((t for t in project.semantic_model.tables if t.name == table_name), None)
        if not table:
            return self._error_response(f"Table '{table_name}' not found")
        
        columns = []
        for column in table.columns:
            columns.append({
                "name": column.name,
                "data_type": column.data_type,
                "summarize_by": column.summarize_by,
                "format_string": column.format_string,
                "is_hidden": column.is_hidden,
                "is_calculated": column.expression is not None,
                "expression": column.expression,
                "lineage_tag": column.lineage_tag,
                "description": column.description
            })
        
        return self._success_response({
            "table_name": table_name,
            "count": len(columns),
            "columns": columns
        })
    
    async def add_column(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Add a new column to a table."""
        project = self._load_project(arguments["project_path"])
        table_name = arguments["table_name"]
        column_name = arguments["column_name"]
        data_type = arguments.get("data_type", "string")
        
        # Validate
        table = next((t for t in project.semantic_model.tables if t.name == table_name), None)
        if not table:
            return self._error_response(f"Table '{table_name}' not found")
        
        if any(c.name == column_name for c in table.columns):
            return self._error_response(f"Column '{column_name}' already exists in table '{table_name}'")
        
        # Read table file
        content = self._read_table_file(arguments["project_path"], table_name)
        
        # Validate DAX expression if provided
        if arguments.get("expression"):
            is_valid, error_msg = self._validate_dax_syntax(arguments["expression"])
            if not is_valid:
                return self._error_response(f"Invalid DAX expression: {error_msg}")
        
        # Format column definition
        column_def = self.tmdl_writer.format_column_definition(
            name=column_name,
            data_type=data_type,
            expression=arguments.get("expression"),
            format_string=arguments.get("format_string"),
            summarize_by=arguments.get("summarize_by"),
            is_hidden=arguments.get("is_hidden", False)
        )
        
        # Add column to TMDL
        updated_content = self.tmdl_writer.add_element(content, "column", column_def)
        
        # Write back
        self._write_table_file(arguments["project_path"], table_name, updated_content)
        
        return self._success_response({
            "success": True,
            "table_name": table_name,
            "column_name": column_name,
            "data_type": data_type,
            "action": "added"
        })
    
    async def update_column(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Update an existing column."""
        project = self._load_project(arguments["project_path"])
        table_name = arguments["table_name"]
        column_name = arguments["column_name"]
        
        # Validate
        table = next((t for t in project.semantic_model.tables if t.name == table_name), None)
        if not table:
            return self._error_response(f"Table '{table_name}' not found")
        
        column = next((c for c in table.columns if c.name == column_name), None)
        if not column:
            return self._error_response(f"Column '{column_name}' not found in table '{table_name}'")
        
        # Read table file
        content = self._read_table_file(arguments["project_path"], table_name)
        
        # Check if column is calculated (has expression)
        is_calculated = hasattr(column, 'expression') and column.expression is not None
        
        # Validate expression changes
        if "expression" in arguments:
            if not is_calculated:
                return self._error_response(
                    f"Cannot add expression to regular column '{column_name}'. "
                    "Create a new calculated column instead."
                )
            if not arguments["expression"]:
                return self._error_response(
                    f"Cannot remove expression from calculated column '{column_name}'. "
                    "Delete the column and create a regular column instead."
                )
        
        # Prepare updates
        updates = {}
        if "data_type" in arguments:
            updates["data_type"] = arguments["data_type"]
        if "format_string" in arguments:
            updates["format_string"] = arguments["format_string"]
        if "summarize_by" in arguments:
            updates["summarize_by"] = arguments["summarize_by"]
        if "is_hidden" in arguments:
            updates["is_hidden"] = arguments["is_hidden"]
        if "expression" in arguments and is_calculated:
            updates["expression"] = arguments["expression"]
        
        # Update TMDL
        updated_content = self.tmdl_writer.update_element(content, "column", column_name, updates)
        
        # Write back
        self._write_table_file(arguments["project_path"], table_name, updated_content)
        
        return self._success_response({
            "success": True,
            "table_name": table_name,
            "column_name": column_name,
            "updated_fields": list(updates.keys())
        })
    
    async def delete_column(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Delete a column from a table."""
        project = self._load_project(arguments["project_path"])
        table_name = arguments["table_name"]
        column_name = arguments["column_name"]
        
        # Validate
        table = next((t for t in project.semantic_model.tables if t.name == table_name), None)
        if not table:
            return self._error_response(f"Table '{table_name}' not found")
        
        if not any(c.name == column_name for c in table.columns):
            return self._error_response(f"Column '{column_name}' not found in table '{table_name}'")
        
        # Read table file
        content = self._read_table_file(arguments["project_path"], table_name)
        
        # Delete column
        updated_content = self.tmdl_writer.delete_element(content, "column", column_name)
        
        # Write back
        self._write_table_file(arguments["project_path"], table_name, updated_content)
        
        return self._success_response({
            "success": True,
            "table_name": table_name,
            "column_name": column_name,
            "action": "deleted"
        })