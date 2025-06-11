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
        """List all columns in a table or all tables."""
        project = self._load_project(arguments["project_path"])
        table_name = arguments.get("table_name")  # Make optional
        
        if table_name:
            # Single table mode (existing behavior)
            normalized_table_name = self._normalize_element_name(table_name)
            table = next((t for t in project.semantic_model.tables if self._normalize_element_name(t.name) == normalized_table_name), None)
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
        else:
            # All tables mode (new functionality)
            all_columns = []
            table_summary = []
            total_columns = 0
            
            for table in project.semantic_model.tables:
                table_columns = []
                for column in table.columns:
                    column_data = {
                        "table_name": table.name,
                        "name": column.name,
                        "data_type": column.data_type,
                        "summarize_by": column.summarize_by,
                        "format_string": column.format_string,
                        "is_hidden": column.is_hidden,
                        "is_calculated": column.expression is not None,
                        "expression": column.expression,
                        "lineage_tag": column.lineage_tag,
                        "description": column.description
                    }
                    table_columns.append(column_data)
                    all_columns.append(column_data)
                
                # Add table summary
                table_summary.append({
                    "table_name": table.name,
                    "column_count": len(table_columns),
                    "calculated_columns": sum(1 for c in table_columns if c["is_calculated"]),
                    "hidden_columns": sum(1 for c in table_columns if c["is_hidden"])
                })
                total_columns += len(table_columns)
            
            return self._success_response({
                "scope": "all_tables",
                "total_tables": len(project.semantic_model.tables),
                "total_columns": total_columns,
                "table_summary": table_summary,
                "columns": all_columns
            })
    
    async def add_column(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Add a new column to a table."""
        project = self._load_project(arguments["project_path"])
        table_name = arguments["table_name"]
        column_name = arguments["column_name"]
        data_type = arguments.get("data_type", "string")
        
        # Validate
        # Find table using normalized name comparison
        normalized_table_name = self._normalize_element_name(table_name)
        table = next((t for t in project.semantic_model.tables if self._normalize_element_name(t.name) == normalized_table_name), None)
        if not table:
            return self._error_response(f"Table '{table_name}' not found")
        
        # Check if column already exists using normalized name comparison
        normalized_input_name = self._normalize_element_name(column_name)
        if any(self._normalize_element_name(c.name) == normalized_input_name for c in table.columns):
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
        # Find table using normalized name comparison
        normalized_table_name = self._normalize_element_name(table_name)
        table = next((t for t in project.semantic_model.tables if self._normalize_element_name(t.name) == normalized_table_name), None)
        if not table:
            return self._error_response(f"Table '{table_name}' not found")
        
        # Find column using normalized name comparison
        normalized_input_name = self._normalize_element_name(column_name)
        column = next((c for c in table.columns if self._normalize_element_name(c.name) == normalized_input_name), None)
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
        
        # Update TMDL using the actual column name from the file
        actual_column_name = column.name
        updated_content = self.tmdl_writer.update_element(content, "column", actual_column_name, updates)
        
        # Write back
        self._write_table_file(arguments["project_path"], table_name, updated_content)
        
        return self._success_response({
            "success": True,
            "table_name": table_name,
            "column_name": actual_column_name,
            "updated_fields": list(updates.keys())
        })
    
    async def delete_column(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Delete a column from a table."""
        project = self._load_project(arguments["project_path"])
        table_name = arguments["table_name"]
        column_name = arguments["column_name"]
        
        # Validate
        # Find table using normalized name comparison
        normalized_table_name = self._normalize_element_name(table_name)
        table = next((t for t in project.semantic_model.tables if self._normalize_element_name(t.name) == normalized_table_name), None)
        if not table:
            return self._error_response(f"Table '{table_name}' not found")
        
        # Find column using normalized name comparison
        normalized_input_name = self._normalize_element_name(column_name)
        target_column = next((c for c in table.columns if self._normalize_element_name(c.name) == normalized_input_name), None)
        if not target_column:
            return self._error_response(f"Column '{column_name}' not found in table '{table_name}'")
        
        # Read table file
        content = self._read_table_file(arguments["project_path"], table_name)
        
        # Delete column using the actual column name from the file
        actual_column_name = target_column.name
        updated_content = self.tmdl_writer.delete_element(content, "column", actual_column_name)
        
        # Write back
        self._write_table_file(arguments["project_path"], table_name, updated_content)
        
        return self._success_response({
            "success": True,
            "table_name": table_name,
            "column_name": actual_column_name,
            "action": "deleted"
        })