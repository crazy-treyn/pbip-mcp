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
        elif operation == OperationType.GET_MODEL_DETAILS:
            return await self.get_model_details(arguments)
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
    
    async def get_model_details(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get comprehensive details of the entire semantic model."""
        project = self._load_project(arguments["project_path"])
        
        # Collect detailed statistics
        total_tables = len(project.semantic_model.tables)
        total_columns = sum(len(t.columns) for t in project.semantic_model.tables)
        total_measures = sum(len(t.measures) for t in project.semantic_model.tables)
        total_relationships = len(project.semantic_model.relationships)
        
        # Data type distribution
        data_type_counts = {}
        calculated_columns = 0
        hidden_columns = 0
        
        # Table details
        table_details = []
        for table in project.semantic_model.tables:
            table_info = {
                "name": table.name,
                "is_hidden": table.is_hidden,
                "is_private": table.is_private,
                "column_count": len(table.columns),
                "measure_count": len(table.measures),
                "hierarchy_count": len(table.hierarchies),
                "partition_count": len(table.partitions),
                "columns": [],
                "measures": []
            }
            
            # Column details
            for column in table.columns:
                if column.expression:
                    calculated_columns += 1
                if column.is_hidden:
                    hidden_columns += 1
                
                # Count data types
                data_type = str(column.data_type)
                data_type_counts[data_type] = data_type_counts.get(data_type, 0) + 1
                
                table_info["columns"].append({
                    "name": column.name,
                    "data_type": data_type,
                    "is_calculated": column.expression is not None,
                    "is_hidden": column.is_hidden,
                    "summarize_by": str(column.summarize_by)
                })
            
            # Measure details
            for measure in table.measures:
                table_info["measures"].append({
                    "name": measure.name,
                    "expression_preview": measure.expression[:100] + "..." if len(measure.expression) > 100 else measure.expression,
                    "is_hidden": measure.is_hidden,
                    "has_format": measure.format_string is not None
                })
            
            table_details.append(table_info)
        
        # Relationship summary
        relationship_summary = {
            "total": total_relationships,
            "active": sum(1 for r in project.semantic_model.relationships if r.is_active),
            "inactive": sum(1 for r in project.semantic_model.relationships if not r.is_active),
            "by_cardinality": {}
        }
        
        for rel in project.semantic_model.relationships:
            cardinality = str(rel.cardinality) if rel.cardinality else "Unknown"
            relationship_summary["by_cardinality"][cardinality] = relationship_summary["by_cardinality"].get(cardinality, 0) + 1
        
        # Build comprehensive response
        overview = {
            "model_name": project.semantic_model.name,
            "culture": project.semantic_model.culture,
            "summary": {
                "tables": {
                    "total": total_tables,
                    "hidden": sum(1 for t in project.semantic_model.tables if t.is_hidden),
                    "private": sum(1 for t in project.semantic_model.tables if t.is_private)
                },
                "columns": {
                    "total": total_columns,
                    "calculated": calculated_columns,
                    "regular": total_columns - calculated_columns,
                    "hidden": hidden_columns,
                    "by_data_type": data_type_counts
                },
                "measures": {
                    "total": total_measures,
                    "hidden": sum(1 for t in project.semantic_model.tables for m in t.measures if m.is_hidden)
                },
                "relationships": relationship_summary
            },
            "tables": table_details
        }
        
        return self._success_response(overview)