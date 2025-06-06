"""Base operation class for PBIP operations."""

from typing import Any, Dict, List
from pathlib import Path
from abc import ABC, abstractmethod

from mcp.types import TextContent
import json
import re

from ..parsers import ProjectParser
from ..writers import TMDLWriter


class OperationType:
    """Standard operation types."""
    LIST = "list"
    GET = "get"
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"


class BaseOperation(ABC):
    """Base class for all PBIP operations."""
    
    def __init__(self, project_parser: ProjectParser = None, tmdl_writer: TMDLWriter = None):
        self.project_parser = project_parser or ProjectParser()
        self.tmdl_writer = tmdl_writer or TMDLWriter()
    
    def _load_project(self, project_path: str):
        """Load and validate project."""
        project = self.project_parser.load_project(project_path)
        if not project.semantic_model:
            raise ValueError("No semantic model found in project")
        return project
    
    def _get_semantic_model_path(self, project_path: str) -> Path:
        """Get semantic model directory path."""
        project_dir = Path(project_path)
        if project_dir.is_file() and project_dir.suffix == ".pbip":
            project_dir = project_dir.parent
        
        # Find semantic model directory
        for pattern in ["*.SemanticModel", "*.Dataset"]:
            dirs = list(project_dir.glob(pattern))
            if dirs:
                return dirs[0]
        
        raise ValueError("Semantic model directory not found")
    
    def _get_table_file_path(self, project_path: str, table_name: str) -> Path:
        """Get path to table TMDL file."""
        model_path = self._get_semantic_model_path(project_path)
        return model_path / "definition" / "tables" / f"{table_name}.tmdl"
    
    def _read_table_file(self, project_path: str, table_name: str) -> str:
        """Read table TMDL file content."""
        table_file = self._get_table_file_path(project_path, table_name)
        if not table_file.exists():
            raise ValueError(f"Table file not found: {table_file}")
        
        with open(table_file, "r", encoding="utf-8") as f:
            return f.read()
    
    def _write_table_file(self, project_path: str, table_name: str, content: str):
        """Write table TMDL file content."""
        table_file = self._get_table_file_path(project_path, table_name)
        with open(table_file, "w", encoding="utf-8") as f:
            f.write(content)
    
    def _success_response(self, data: Any, message: str = None) -> List[TextContent]:
        """Create standardized success response."""
        if message:
            return [TextContent(type="text", text=message)]
        
        if isinstance(data, (dict, list)):
            return [TextContent(type="text", text=json.dumps(data, indent=2))]
        
        return [TextContent(type="text", text=str(data))]
    
    def _error_response(self, message: str) -> List[TextContent]:
        """Create standardized error response."""
        return [TextContent(type="text", text=f"Error: {message}")]
    
    def _validate_dax_syntax(self, expression: str) -> tuple[bool, str]:
        """Basic DAX syntax validation.
        
        Returns:
            (is_valid, error_message)
        """
        if not expression or not expression.strip():
            return False, "DAX expression cannot be empty"
        
        # Check for balanced parentheses
        paren_count = 0
        for char in expression:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            if paren_count < 0:
                return False, "Unmatched closing parenthesis"
        
        if paren_count != 0:
            return False, "Unmatched opening parenthesis"
        
        # Check for balanced square brackets
        bracket_count = 0
        for char in expression:
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
            if bracket_count < 0:
                return False, "Unmatched closing bracket"
        
        if bracket_count != 0:
            return False, "Unmatched opening bracket"
        
        # Check for balanced quotes
        quote_matches = re.findall(r'"[^"]*"', expression)
        expression_without_quotes = expression
        for match in quote_matches:
            expression_without_quotes = expression_without_quotes.replace(match, '', 1)
        
        if '"' in expression_without_quotes:
            return False, "Unmatched quotes"
        
        # Basic checks for common DAX errors
        if expression.strip().endswith(','):
            return False, "Expression cannot end with a comma"
        
        # Check for empty function calls
        if '()' in expression:
            return False, "Empty function calls are not allowed"
        
        return True, ""
    
    @abstractmethod
    async def execute(self, operation: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the specified operation."""
        raise NotImplementedError("Subclasses must implement execute()")