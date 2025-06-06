"""TMDL file writer with support for various operations."""

import re
from typing import Any, Dict, List, Optional
import uuid


class TMDLWriter:
    """Handles writing operations for TMDL files."""
    
    def add_element(self, content: str, element_type: str, element_def: str, 
                    parent_context: Dict[str, Any] = None) -> str:
        """Add a new element to TMDL content."""
        lines = content.split("\n")
        
        # Find insertion point based on element type
        insert_position = self._find_insertion_point(lines, element_type, parent_context)
        
        # Insert the new element
        indent_level = parent_context.get("indent_level", 1) if parent_context else 1
        indent = "\t" * indent_level
        
        # Split element definition into lines and add proper indentation
        element_lines = element_def.strip().split("\n")
        for i, line in enumerate(element_lines):
            if i == 0:
                lines.insert(insert_position + i, f"{indent}{line}")
            else:
                # Sub-properties get additional indentation
                lines.insert(insert_position + i, f"{indent}{line}")
        
        # Add empty line after element if needed
        if insert_position + len(element_lines) < len(lines):
            if lines[insert_position + len(element_lines)].strip():
                lines.insert(insert_position + len(element_lines), "")
        
        return "\n".join(lines)
    
    def update_element(self, content: str, element_type: str, element_name: str, 
                      updates: Dict[str, Any]) -> str:
        """Update an existing element in TMDL content."""
        lines = content.split("\n")
        updated_lines = []
        in_element = False
        element_indent = 0
        properties_updated = set()
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if self._is_element_definition(line, element_type, element_name):
                in_element = True
                element_indent = self._get_indentation(line)
                
                # Handle expression updates for measures and calculated columns
                if element_type in ["measure", "column"] and "expression" in updates:
                    updated_line = self._update_expression_line(line, updates["expression"])
                    updated_lines.append(updated_line)
                    properties_updated.add("expression")
                else:
                    updated_lines.append(line)
                i += 1
                continue
            
            if in_element:
                line_indent = self._get_indentation(line)
                
                # Check if we've exited the element
                if line.strip() and line_indent <= element_indent:
                    in_element = False
                    # Add any new properties before exiting
                    self._add_new_properties(updated_lines, element_indent + 1, updates, properties_updated)
                    updated_lines.append(line)
                    i += 1
                    continue
                
                # Update existing properties
                property_updated = False
                for prop, value in updates.items():
                    if prop == "expression":
                        continue  # Already handled
                    
                    tmdl_prop = self._to_tmdl_property_name(prop)
                    if line.strip().startswith(f"{tmdl_prop}:"):
                        indent = '\t' * (element_indent + 1)
                        updated_lines.append(f"{indent}{tmdl_prop}: {self._format_value(value)}")
                        properties_updated.add(prop)
                        property_updated = True
                        break
                
                if not property_updated:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
            
            i += 1
        
        # Handle case where element is at end of file
        if in_element:
            self._add_new_properties(updated_lines, element_indent + 1, updates, properties_updated)
        
        return "\n".join(updated_lines)
    
    def delete_element(self, content: str, element_type: str, element_name: str) -> str:
        """Delete an element from TMDL content."""
        lines = content.split("\n")
        filtered_lines = []
        in_element = False
        element_indent = 0
        skip_empty_after = False
        
        # Also track if we need to remove description comments
        removing_description = False
        description_indent = 0
        
        for i, line in enumerate(lines):
            # Check for description comments before element
            if not in_element and i + 1 < len(lines):
                next_line = lines[i + 1]
                if self._is_element_definition(next_line, element_type, element_name):
                    if line.strip().startswith("///"):
                        removing_description = True
                        description_indent = self._get_indentation(line)
                        continue
            
            # Continue removing description lines
            if removing_description:
                if line.strip().startswith("///") and self._get_indentation(line) == description_indent:
                    continue
                else:
                    removing_description = False
            
            if self._is_element_definition(line, element_type, element_name):
                in_element = True
                element_indent = self._get_indentation(line)
                skip_empty_after = True
                continue
            
            if in_element:
                line_indent = self._get_indentation(line)
                if line.strip() and line_indent <= element_indent:
                    in_element = False
                else:
                    continue
            
            # Skip empty line immediately after deleted element
            if skip_empty_after and not line.strip():
                skip_empty_after = False
                continue
            
            skip_empty_after = False
            filtered_lines.append(line)
        
        return "\n".join(filtered_lines)
    
    def add_description_comments(self, content: str, element_type: str, element_name: str, 
                               description: str) -> str:
        """Add or update description comments for an element."""
        lines = content.split("\n")
        updated_lines = []
        
        # Split description into comment lines
        description_lines = self._split_description_for_comments(description)
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this is our target element
            if self._is_element_definition(line, element_type, element_name):
                element_indent = self._get_indentation(line)
                indent_str = "\t" * element_indent
                
                # Remove any existing description comments immediately before
                while updated_lines and updated_lines[-1].strip().startswith("///"):
                    updated_lines.pop()
                
                # Add new description comments
                for desc_line in description_lines:
                    updated_lines.append(f"{indent_str}/// {desc_line}")
                
                updated_lines.append(line)
            else:
                updated_lines.append(line)
            
            i += 1
        
        return "\n".join(updated_lines)
    
    def format_measure_definition(self, name: str, expression: str, 
                                description: Optional[str] = None,
                                format_string: Optional[str] = None,
                                lineage_tag: Optional[str] = None) -> str:
        """Format a complete measure definition."""
        if not lineage_tag:
            lineage_tag = str(uuid.uuid4())
        
        lines = []
        
        # Add description as comments
        if description:
            for desc_line in self._split_description_for_comments(description):
                lines.append(f"/// {desc_line}")
        
        # Add measure definition
        formatted_name = self._format_element_name(name)
        lines.append(f"measure {formatted_name} = {expression}")
        lines.append(f"\tlineageTag: {lineage_tag}")
        
        # Add optional properties
        if format_string:
            lines.append(f'\tformatString: "{format_string}"')
        
        return "\n".join(lines)
    
    def format_column_definition(self, name: str, data_type: str,
                               expression: Optional[str] = None,
                               format_string: Optional[str] = None,
                               summarize_by: Optional[str] = None,
                               is_hidden: bool = False,
                               lineage_tag: Optional[str] = None) -> str:
        """Format a complete column definition."""
        if not lineage_tag:
            lineage_tag = str(uuid.uuid4())
        
        lines = []
        
        # Add column definition
        formatted_name = self._format_element_name(name)
        if expression:
            lines.append(f"column {formatted_name} = {expression}")
        else:
            lines.append(f"column {formatted_name}")
        
        # Add required properties
        lines.append(f"\tdataType: {data_type}")
        lines.append(f"\tlineageTag: {lineage_tag}")
        
        # Add optional properties
        if format_string:
            lines.append(f'\tformatString: "{format_string}"')
        
        if summarize_by:
            lines.append(f"\tsummarizeBy: {summarize_by}")
        
        if is_hidden:
            lines.append("\tisHidden")
        
        return "\n".join(lines)
    
    def _find_insertion_point(self, lines: list, element_type: str, 
                            context: Dict[str, Any] = None) -> int:
        """Find the appropriate insertion point for a new element."""
        last_similar_element = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{element_type} "):
                last_similar_element = i
                # Find end of this element block
                j = i + 1
                element_indent = self._get_indentation(line)
                while j < len(lines):
                    if lines[j].strip() and self._get_indentation(lines[j]) <= element_indent:
                        break
                    j += 1
                last_similar_element = j - 1
        
        if last_similar_element >= 0:
            # Insert after the last similar element
            return last_similar_element + 1
        
        # Default positions based on element type
        if element_type == "measure":
            # Insert after table definition but before columns
            for i, line in enumerate(lines):
                if line.strip().startswith("column ") or line.strip().startswith("partition "):
                    return i
        elif element_type == "column":
            # Insert after last column but before partitions
            for i, line in enumerate(lines):
                if line.strip().startswith("partition "):
                    return i
        
        # Default: insert near the end
        return max(0, len(lines) - 3)
    
    def _is_element_definition(self, line: str, element_type: str, element_name: str) -> bool:
        """Check if a line defines the specified element."""
        if not line.strip().startswith(f"{element_type} "):
            return False
        
        # Extract element name from line
        if element_type == "measure":
            match = re.match(r"measure\s+(.+?)\s*=", line.strip())
            if match:
                found_name = match.group(1).strip().strip("'\"")
                return found_name == element_name.strip("'\"")
        elif element_type == "column":
            match = re.match(r"column\s+(.+?)(\s*=|$)", line.strip())
            if match:
                found_name = match.group(1).strip().strip("'\"")
                return found_name == element_name.strip("'\"")
        elif element_type == "table":
            match = re.match(r"table\s+(.+?)$", line.strip())
            if match:
                found_name = match.group(1).strip().strip("'\"")
                return found_name == element_name.strip("'\"")
        
        return False
    
    def _get_indentation(self, line: str) -> int:
        """Get indentation level of a line."""
        return len(line) - len(line.lstrip("\t"))
    
    def _update_expression_line(self, line: str, new_expression: str) -> str:
        """Update the expression part of a definition line."""
        if " = " in line:
            prefix = line.split(" = ", 1)[0]
            return f"{prefix} = {new_expression}"
        return line
    
    def _format_value(self, value: Any) -> str:
        """Format a value for TMDL."""
        if isinstance(value, str):
            # Don't double-quote if already quoted
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                return value
            return f'"{value}"'
        elif isinstance(value, bool):
            return "true" if value else "false"
        else:
            return str(value)
    
    def _format_element_name(self, name: str) -> str:
        """Format element name, adding quotes if needed."""
        # If already quoted, return as-is
        if (name.startswith("'") and name.endswith("'")) or \
           (name.startswith('"') and name.endswith('"')):
            return name
        
        # Check if name needs quotes
        needs_quotes = False
        if " " in name or any(char in name for char in ".-+*/()[]{}@#$%^&"):
            needs_quotes = True
        
        # Also check if name is a reserved word
        reserved_words = ["table", "column", "measure", "partition", "relationship"]
        if name.lower() in reserved_words:
            needs_quotes = True
        
        return f"'{name}'" if needs_quotes else name
    
    def _to_tmdl_property_name(self, property_name: str) -> str:
        """Convert property name to TMDL format."""
        # Map common property names
        property_map = {
            "format_string": "formatString",
            "data_type": "dataType",
            "summarize_by": "summarizeBy",
            "is_hidden": "isHidden",
            "lineage_tag": "lineageTag",
            "source_column": "sourceColumn",
        }
        
        return property_map.get(property_name, property_name)
    
    def _add_new_properties(self, lines: list, indent_level: int, 
                          properties: Dict[str, Any], existing_properties: set):
        """Add new properties that don't exist yet."""
        indent = "\t" * indent_level
        
        for prop, value in properties.items():
            if prop not in existing_properties and prop not in ["expression", "name"]:
                tmdl_prop = self._to_tmdl_property_name(prop)
                
                # Handle boolean flags
                if isinstance(value, bool) and value and tmdl_prop in ["isHidden", "isPrivate"]:
                    lines.append(f"{indent}{tmdl_prop}")
                else:
                    lines.append(f"{indent}{tmdl_prop}: {self._format_value(value)}")
    
    def _split_description_for_comments(self, description: str) -> List[str]:
        """Split description into appropriate lines for TMDL comments."""
        if not description:
            return []
        
        import textwrap
        
        # First split by sentences to keep logical breaks
        sentences = description.replace(". ", ".\n").split("\n")
        lines = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Wrap long sentences
            wrapped = textwrap.fill(
                sentence, 
                width=80, 
                break_long_words=False, 
                break_on_hyphens=False
            )
            lines.extend(wrapped.split("\n"))
        
        return [line.strip() for line in lines if line.strip()]