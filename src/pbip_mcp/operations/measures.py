"""Measure operations for PBIP MCP Server."""

from typing import Any, Dict, List
import uuid

from mcp.types import TextContent

from .base import BaseOperation, OperationType


class MeasureOperations(BaseOperation):
    """Handle all measure-related operations."""
    
    async def execute(self, operation: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the specified measure operation."""
        if operation == OperationType.LIST:
            return await self.list_measures(arguments)
        elif operation == OperationType.ADD:
            return await self.add_measure(arguments)
        elif operation == OperationType.UPDATE:
            return await self.update_measure(arguments)
        elif operation == OperationType.DELETE:
            return await self.delete_measure(arguments)
        else:
            return self._error_response(f"Unknown operation: {operation}")
    
    async def list_measures(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List all measures in the project."""
        project = self._load_project(arguments["project_path"])
        table_name = arguments.get("table_name")
        
        measures = []
        for table in project.semantic_model.tables:
            if table_name and table.name != table_name:
                continue
            
            for measure in table.measures:
                measures.append({
                    "table_name": table.name,
                    "name": measure.name,
                    "expression": measure.expression,
                    "format_string": measure.format_string,
                    "lineage_tag": measure.lineage_tag,
                    "is_hidden": measure.is_hidden,
                    "description": measure.description
                })
        
        return self._success_response({
            "count": len(measures),
            "measures": measures
        })
    
    async def add_measure(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Add a new measure to a table."""
        project = self._load_project(arguments["project_path"])
        table_name = arguments["table_name"]
        measure_name = arguments["measure_name"]
        expression = arguments["expression"]
        
        # Validate table exists using normalized name comparison
        normalized_table_name = self._normalize_element_name(table_name)
        table = next((t for t in project.semantic_model.tables if self._normalize_element_name(t.name) == normalized_table_name), None)
        if not table:
            return self._error_response(f"Table '{table_name}' not found")
        
        # Check if measure already exists (across all tables)
        normalized_input_name = self._normalize_element_name(measure_name)
        for t in project.semantic_model.tables:
            if any(self._normalize_element_name(m.name) == normalized_input_name for m in t.measures):
                return self._error_response(f"Measure '{measure_name}' already exists in table '{t.name}'")
        
        # Validate DAX expression
        is_valid, error_msg = self._validate_dax_syntax(expression)
        if not is_valid:
            return self._error_response(f"Invalid DAX expression: {error_msg}")
        
        # Read table file
        content = self._read_table_file(arguments["project_path"], table_name)
        
        # Format measure definition
        measure_def = self.tmdl_writer.format_measure_definition(
            name=measure_name,
            expression=expression,
            description=arguments.get("description"),
            format_string=arguments.get("format_string")
        )
        
        # Add measure to TMDL
        updated_content = self.tmdl_writer.add_element(content, "measure", measure_def)
        
        # Write back
        self._write_table_file(arguments["project_path"], table_name, updated_content)
        
        return self._success_response({
            "success": True,
            "table_name": table_name,
            "measure_name": measure_name,
            "action": "added"
        })
    
    async def update_measure(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Update an existing measure."""
        project = self._load_project(arguments["project_path"])
        table_name = arguments["table_name"]
        measure_name = arguments["measure_name"]
        
        # Find the table using normalized name comparison
        normalized_table_name = self._normalize_element_name(table_name)
        table = next((t for t in project.semantic_model.tables if self._normalize_element_name(t.name) == normalized_table_name), None)
        if not table:
            return self._error_response(f"Table '{table_name}' not found")
        
        # Find measure using normalized name comparison
        normalized_input_name = self._normalize_element_name(measure_name)
        measure = next((m for m in table.measures if self._normalize_element_name(m.name) == normalized_input_name), None)
        if not measure:
            return self._error_response(f"Measure '{measure_name}' not found in table '{table_name}'")
        
        # Read table file
        content = self._read_table_file(arguments["project_path"], table_name)
        
        # Prepare updates
        updates = {}
        if "expression" in arguments:
            # Validate DAX expression
            is_valid, error_msg = self._validate_dax_syntax(arguments["expression"])
            if not is_valid:
                return self._error_response(f"Invalid DAX expression: {error_msg}")
            updates["expression"] = arguments["expression"]
        if "format_string" in arguments:
            updates["format_string"] = arguments["format_string"]
        
        # Update TMDL using the actual measure name from the file
        actual_measure_name = measure.name
        updated_content = self.tmdl_writer.update_element(content, "measure", actual_measure_name, updates)
        
        # Handle description separately (as comments)
        if "description" in arguments:
            updated_content = self.tmdl_writer.add_description_comments(
                updated_content, "measure", actual_measure_name, arguments["description"]
            )
        
        # Write back
        self._write_table_file(arguments["project_path"], table_name, updated_content)
        
        return self._success_response({
            "success": True,
            "table_name": table_name,
            "measure_name": actual_measure_name,
            "updated_fields": list(updates.keys()) + (["description"] if "description" in arguments else [])
        })
    
    async def delete_measure(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Delete a measure from a table."""
        project = self._load_project(arguments["project_path"])
        table_name = arguments["table_name"]
        measure_name = arguments["measure_name"]
        
        # Validate table exists using normalized name comparison
        normalized_table_name = self._normalize_element_name(table_name)
        table = next((t for t in project.semantic_model.tables if self._normalize_element_name(t.name) == normalized_table_name), None)
        if not table:
            return self._error_response(f"Table '{table_name}' not found")
        
        # Find measure using normalized name comparison
        normalized_input_name = self._normalize_element_name(measure_name)
        target_measure = next((m for m in table.measures if self._normalize_element_name(m.name) == normalized_input_name), None)
        if not target_measure:
            return self._error_response(f"Measure '{measure_name}' not found in table '{table_name}'")
        
        # Read table file
        content = self._read_table_file(arguments["project_path"], table_name)
        
        # Delete measure using the actual measure name from the file
        actual_measure_name = target_measure.name
        updated_content = self.tmdl_writer.delete_element(content, "measure", actual_measure_name)
        
        # Write back
        self._write_table_file(arguments["project_path"], table_name, updated_content)
        
        return self._success_response({
            "success": True,
            "table_name": table_name,
            "measure_name": actual_measure_name,
            "action": "deleted"
        })