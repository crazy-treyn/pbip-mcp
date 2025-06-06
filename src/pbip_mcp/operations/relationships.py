"""Relationship operations for PBIP MCP Server."""

from typing import Any, Dict, List

from mcp.types import TextContent

from .base import BaseOperation, OperationType


class RelationshipOperations(BaseOperation):
    """Handle relationship operations."""
    
    async def execute(self, operation: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the specified relationship operation."""
        if operation == OperationType.LIST:
            return await self.list_relationships(arguments)
        else:
            return self._error_response(f"Unknown operation: {operation}")
    
    async def list_relationships(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List all relationships in the project."""
        project = self._load_project(arguments["project_path"])
        
        relationships = []
        for rel in project.semantic_model.relationships:
            relationships.append({
                "name": rel.name,
                "from": f"{rel.from_table}[{rel.from_column}]",
                "to": f"{rel.to_table}[{rel.to_column}]",
                "cardinality": rel.cardinality,
                "cross_filtering_behavior": rel.cross_filtering_behavior,
                "is_active": rel.is_active,
                "join_on_date_behavior": rel.join_on_date_behavior
            })
        
        # Group by cardinality for summary
        cardinality_summary = {}
        for rel in relationships:
            card = rel["cardinality"]
            if card not in cardinality_summary:
                cardinality_summary[card] = 0
            cardinality_summary[card] += 1
        
        return self._success_response({
            "count": len(relationships),
            "active_count": sum(1 for r in relationships if r["is_active"]),
            "inactive_count": sum(1 for r in relationships if not r["is_active"]),
            "cardinality_summary": cardinality_summary,
            "relationships": relationships
        })