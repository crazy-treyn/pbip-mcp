"""TMDL (Tabular Model Definition Language) parser."""

import re
from typing import Any, Dict, List, Optional, Tuple, Union

from ..models import (
    Annotation,
    CalculationGroup,
    CalculationItem,
    Column,
    CultureInfo,
    DataType,
    Database,
    Hierarchy,
    HierarchyLevel,
    Measure,
    Partition,
    PartitionMode,
    Relationship,
    SemanticModel,
    SummarizeBy,
    Table,
    Variation,
)


class TMDLParseError(Exception):
    """Error parsing TMDL content."""

    def __init__(self, message: str, line_number: Optional[int] = None):
        self.line_number = line_number
        super().__init__(f"Line {line_number}: {message}" if line_number else message)


class TMDLParser:
    """Parser for TMDL files."""

    def __init__(self):
        self.current_line = 0
        self.lines: List[str] = []
        self.description_buffer: List[str] = []

    def parse_file(self, content: str) -> Dict[str, Any]:
        """Parse TMDL file content."""
        self.lines = content.split("\n")
        self.current_line = 0

        result = {}

        while self.current_line < len(self.lines):
            line = self._get_current_line().strip()

            if not line:
                self._advance_line()
                continue
                
            # Handle triple-slash comments as descriptions
            if line.startswith("///"):
                # Extract the description text after "/// "
                desc_text = line[3:].strip()
                self.description_buffer.append(desc_text)
                self._advance_line()
                continue
            elif line.startswith("//"):
                # Regular comments - ignore and clear description buffer
                self.description_buffer.clear()
                self._advance_line()
                continue
            
            # If we have a non-comment line, we need to process it
            # The description buffer will be consumed by the relevant parser

            # Parse top-level elements
            if line.startswith("model "):
                result["model"] = self._parse_model()
            elif line.startswith("table "):
                if "tables" not in result:
                    result["tables"] = []
                # Capture description before parsing
                table_description = " ".join(self.description_buffer) if self.description_buffer else None
                self.description_buffer.clear()
                
                table = self._parse_table()
                if table_description:
                    table["description"] = table_description
                result["tables"].append(table)
            elif line.startswith("relationship "):
                if "relationships" not in result:
                    result["relationships"] = []
                result["relationships"].append(self._parse_relationship())
            elif line.startswith("cultureInfo "):
                if "culture_infos" not in result:
                    result["culture_infos"] = []
                result["culture_infos"].append(self._parse_culture_info())
            elif line.startswith("database"):
                result["database"] = self._parse_database()
            elif line.startswith("annotation "):
                if "annotations" not in result:
                    result["annotations"] = []
                result["annotations"].append(self._parse_annotation())
            elif line.startswith("ref table "):
                # Table reference at top level
                if "table_refs" not in result:
                    result["table_refs"] = []
                table_name = line.replace("ref table ", "").strip()
                result["table_refs"].append(table_name)
                self._advance_line()
            elif line.startswith("ref cultureInfo "):
                # Culture reference at top level
                if "culture_refs" not in result:
                    result["culture_refs"] = []
                culture_name = line.replace("ref cultureInfo ", "").strip()
                result["culture_refs"].append(culture_name)
                self._advance_line()
            elif line.strip() and not line.startswith("//"):
                # Unrecognized syntax that isn't empty or comment
                # Clear description buffer on unrecognized lines
                self.description_buffer.clear()
                raise TMDLParseError(
                    f"Unrecognized TMDL syntax: {line}", self.current_line + 1
                )
            else:
                # Clear description buffer on other lines
                self.description_buffer.clear()
                self._advance_line()

        return result

    def _get_current_line(self) -> str:
        """Get current line content."""
        if self.current_line >= len(self.lines):
            return ""
        return self.lines[self.current_line]

    def _advance_line(self):
        """Move to next line."""
        self.current_line += 1

    def _get_indentation(self, line: str) -> int:
        """Get indentation level of line."""
        return len(line) - len(line.lstrip("\t "))

    def _parse_model(self) -> Dict[str, Any]:
        """Parse model definition."""
        line = self._get_current_line().strip()
        match = re.match(r"model\s+(.+)", line)
        if not match:
            raise TMDLParseError("Invalid model definition", self.current_line + 1)

        model_name = match.group(1).strip()
        if not model_name:
            raise TMDLParseError("Model name cannot be empty", self.current_line + 1)

        self._advance_line()

        model = {
            "name": model_name,
            "tables": [],
            "relationships": [],
            "culture_infos": [],
            "annotations": [],
        }

        base_indent = None

        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None:
                base_indent = indent
            elif indent <= 0:  # Back to top level
                break

            line_content = line.strip()

            if line_content.startswith("culture:"):
                model["culture"] = self._parse_property_value(line_content)
            elif line_content.startswith("defaultPowerBIDataSourceVersion:"):
                model["default_power_bi_data_source_version"] = (
                    self._parse_property_value(line_content)
                )
            elif line_content.startswith("discourageImplicitMeasures"):
                model["discourage_implicit_measures"] = True
            elif line_content.startswith("sourceQueryCulture:"):
                model["source_query_culture"] = self._parse_property_value(line_content)
            elif line_content.startswith("annotation "):
                model["annotations"].append(self._parse_annotation())
                continue  # _parse_annotation advances the line
            elif line_content.startswith("ref table "):
                # Table reference - we'll load the actual table later
                table_name = line_content.replace("ref table ", "").strip()
                model["table_refs"] = model.get("table_refs", [])
                model["table_refs"].append(table_name)
            elif line_content.startswith("ref cultureInfo "):
                # Culture reference
                culture_name = line_content.replace("ref cultureInfo ", "").strip()
                model["culture_refs"] = model.get("culture_refs", [])
                model["culture_refs"].append(culture_name)
            elif line_content.startswith("dataAccessOptions"):
                model["data_access_options"] = self._parse_data_access_options()
                continue  # _parse_data_access_options advances the line

            self._advance_line()

        return model

    def _parse_table(self) -> Dict[str, Any]:
        """Parse table definition."""
        line = self._get_current_line().strip()
        match = re.match(r"table\s+(.+)", line)
        if not match:
            raise TMDLParseError("Invalid table definition", self.current_line + 1)

        table_name = match.group(1).strip()
        if not table_name:
            raise TMDLParseError("Table name cannot be empty", self.current_line + 1)

        self._advance_line()

        table = {
            "name": table_name,
            "columns": [],
            "measures": [],
            "hierarchies": [],
            "partitions": [],
            "annotations": [],
            "is_hidden": False,
            "is_private": False,
            "show_as_variations_only": False,
        }

        base_indent = None

        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None and line.strip():
                base_indent = indent
            elif indent <= 0:  # Back to top level
                break

            line_content = line.strip()
            
            # Handle triple-slash comments inside table
            if line_content.startswith("///"):
                desc_text = line_content[3:].strip()
                self.description_buffer.append(desc_text)
                self._advance_line()
                continue
            elif line_content.startswith("//"):
                # Regular comment - clear description buffer
                self.description_buffer.clear()
                self._advance_line()
                continue

            if line_content.startswith("lineageTag:"):
                table["lineage_tag"] = self._parse_property_value(line_content)
            elif line_content.startswith("isHidden"):
                table["is_hidden"] = True
            elif line_content.startswith("isPrivate"):
                table["is_private"] = True
            elif line_content.startswith("showAsVariationsOnly"):
                table["show_as_variations_only"] = True
            elif line_content.startswith("column "):
                # Capture description before parsing
                column_description = " ".join(self.description_buffer) if self.description_buffer else None
                self.description_buffer.clear()
                
                column = self._parse_column()
                if column_description:
                    column["description"] = column_description
                table["columns"].append(column)
                continue
            elif line_content.startswith("measure "):
                # Capture description before parsing
                measure_description = " ".join(self.description_buffer) if self.description_buffer else None
                self.description_buffer.clear()
                
                measure = self._parse_measure()
                if measure is not None:  # Only add valid measures
                    if measure_description:
                        measure["description"] = measure_description
                    table["measures"].append(measure)
                continue
            elif line_content.startswith("hierarchy "):
                table["hierarchies"].append(self._parse_hierarchy())
                continue
            elif line_content.startswith("partition "):
                table["partitions"].append(self._parse_partition())
                continue
            elif line_content.startswith("calculationGroup"):
                table["calculation_group"] = self._parse_calculation_group()
                continue
            elif line_content.startswith("annotation "):
                table["annotations"].append(self._parse_annotation())
                continue
            else:
                # Clear description buffer on non-description lines
                self.description_buffer.clear()

            self._advance_line()

        return table

    def _parse_column(self) -> Dict[str, Any]:
        """Parse column definition."""
        line = self._get_current_line().strip()

        # Handle both regular columns and calculated columns
        if " = " in line:
            # Calculated column: column Name = Expression
            match = re.match(r"column\s+(.+?)\s*=\s*(.+)", line)
            if not match:
                raise TMDLParseError(
                    "Invalid calculated column definition", self.current_line + 1
                )
            column_name = match.group(1).strip()
            expression = match.group(2).strip()
            is_calculated = True
        else:
            # Regular column: column Name
            match = re.match(r"column\s+(.+)", line)
            if not match:
                raise TMDLParseError("Invalid column definition", self.current_line + 1)
            column_name = match.group(1).strip()
            expression = None
            is_calculated = False

        # Remove quotes if present
        if (column_name.startswith("'") and column_name.endswith("'")) or (
            column_name.startswith('"') and column_name.endswith('"')
        ):
            column_name = column_name[1:-1]

        self._advance_line()

        column = {
            "name": column_name,
            "lineage_tag": "",
            "data_type": DataType.STRING,
            "summarize_by": SummarizeBy.NONE,
            "annotations": [],
            "is_hidden": False,
            "is_name_inferred": False,
        }

        if is_calculated:
            column["expression"] = expression

        base_indent = None

        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None and line.strip():
                base_indent = indent
            elif (
                indent <= base_indent
                and line.strip()
                and not line.strip().startswith(("annotation", "variation"))
            ):
                break

            line_content = line.strip()

            if line_content.startswith("dataType:"):
                column["data_type"] = self._parse_property_value(line_content)
            elif line_content.startswith("lineageTag:"):
                column["lineage_tag"] = self._parse_property_value(line_content)
            elif line_content.startswith("summarizeBy:"):
                column["summarize_by"] = self._parse_property_value(line_content)
            elif line_content.startswith("formatString:"):
                column["format_string"] = self._parse_property_value(line_content)
            elif line_content.startswith("sourceColumn:"):
                column["source_column"] = self._parse_property_value(line_content)
            elif line_content.startswith("dataCategory:"):
                column["data_category"] = self._parse_property_value(line_content)
            elif line_content.startswith("sortByColumn:"):
                column["sort_by_column"] = self._parse_property_value(line_content)
            elif line_content.startswith("isHidden"):
                column["is_hidden"] = True
            elif line_content.startswith("isNameInferred"):
                column["is_name_inferred"] = True
            elif line_content.startswith("annotation "):
                column["annotations"].append(self._parse_annotation())
                continue
            elif line_content.startswith("variation "):
                column["variation"] = self._parse_variation()
                continue

            self._advance_line()

        return column

    def _parse_measure(self) -> Optional[Dict[str, Any]]:
        """Parse measure definition with error recovery."""
        line = self._get_current_line().strip()
        match = re.match(r"measure\s+(.+?)\s*=\s*(.+)", line)
        if not match:
            # Try to skip malformed measure and continue parsing
            self._advance_line()
            # Skip any properties that belong to this malformed measure
            self._skip_measure_properties()
            return None

        measure_name = match.group(1).strip()
        expression = match.group(2).strip()
        
        # Validate that measure name has proper quotes if it contains spaces
        if " " in measure_name and not ((measure_name.startswith("'") and measure_name.endswith("'")) or 
                                       (measure_name.startswith('"') and measure_name.endswith('"'))):
            self._advance_line()
            self._skip_measure_properties()
            return None
            
        self._advance_line()

        measure = {
            "name": measure_name,
            "expression": expression,
            "lineage_tag": "",
            "annotations": [],
            "is_hidden": False,
        }

        base_indent = None

        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None and line.strip():
                base_indent = indent
            elif (
                indent <= base_indent
                and line.strip()
                and not line.strip().startswith("annotation")
            ):
                break

            line_content = line.strip()

            if line_content.startswith("lineageTag:"):
                measure["lineage_tag"] = self._parse_property_value(line_content)
            elif line_content.startswith("formatString:"):
                measure["format_string"] = self._parse_property_value(line_content)
            elif line_content.startswith("isHidden"):
                measure["is_hidden"] = True
            elif line_content.startswith("annotation "):
                # Skip annotation Description since we now use /// comments
                annotation = self._parse_annotation()
                if annotation["name"] != "Description":
                    measure["annotations"].append(annotation)
                continue
            elif line_content.startswith("changedProperty"):
                # Skip changedProperty lines - these are metadata we don't need
                pass
            elif line_content.startswith("displayFolder:"):
                measure["display_folder"] = self._parse_property_value(line_content)

            self._advance_line()

        return measure
    
    def _skip_measure_properties(self):
        """Skip properties belonging to a malformed measure."""
        base_indent = None
        
        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue
                
            indent = self._get_indentation(line)
            
            if base_indent is None and line.strip():
                base_indent = indent
            elif indent <= base_indent and line.strip():
                # We've reached the next element at the same or lower level
                break
                
            self._advance_line()

    def _parse_relationship(self) -> Dict[str, Any]:
        """Parse relationship definition."""
        line = self._get_current_line().strip()
        match = re.match(r"relationship\s+(.+)", line)
        if not match:
            raise TMDLParseError(
                "Invalid relationship definition", self.current_line + 1
            )

        relationship_name = match.group(1)
        self._advance_line()

        relationship = {"name": relationship_name, "is_active": True}

        base_indent = None

        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None and line.strip():
                base_indent = indent
            elif indent <= 0:
                break

            line_content = line.strip()

            if line_content.startswith("fromColumn:"):
                from_ref = self._parse_property_value(line_content)
                if "." in from_ref:
                    table, column = from_ref.split(".", 1)
                    relationship["from_table"] = table
                    relationship["from_column"] = column
            elif line_content.startswith("toColumn:"):
                to_ref = self._parse_property_value(line_content)
                if "." in to_ref:
                    table, column = to_ref.split(".", 1)
                    relationship["to_table"] = table
                    relationship["to_column"] = column
            elif line_content.startswith("joinOnDateBehavior:"):
                relationship["join_on_date_behavior"] = self._parse_property_value(
                    line_content
                )
            elif line_content.startswith("cardinality:"):
                relationship["cardinality"] = self._parse_property_value(line_content)
            elif line_content.startswith("crossFilteringBehavior:"):
                relationship["cross_filtering_behavior"] = self._parse_property_value(
                    line_content
                )
            elif line_content.startswith("isActive:"):
                relationship["is_active"] = (
                    self._parse_property_value(line_content).lower() == "true"
                )

            self._advance_line()

        return relationship

    def _parse_annotation(self) -> Dict[str, Any]:
        """Parse annotation."""
        line = self._get_current_line().strip()
        match = re.match(r"annotation\s+(.+?)\s*=\s*(.+)", line)
        if not match:
            raise TMDLParseError("Invalid annotation definition", self.current_line + 1)

        name = match.group(1)
        value_str = match.group(2)

        # Parse the value
        value = self._parse_annotation_value(value_str)

        self._advance_line()

        return {"name": name, "value": value}

    def _parse_annotation_value(self, value_str: str) -> Any:
        """Parse annotation value."""
        value_str = value_str.strip()

        # String value (quoted)
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        elif value_str.startswith("'") and value_str.endswith("'"):
            return value_str[1:-1]

        # JSON object/array
        if value_str.startswith(("{", "[")):
            try:
                import json

                return json.loads(value_str)
            except json.JSONDecodeError:
                return value_str

        # Boolean
        if value_str.lower() in ("true", "false"):
            return value_str.lower() == "true"

        # Number
        try:
            if "." in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        # Default to string
        return value_str

    def _parse_calculation_group(self) -> Dict[str, Any]:
        """Parse calculation group."""
        self._advance_line()  # Skip the "calculationGroup" line

        calc_group = {"calculation_items": []}

        base_indent = None

        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None and line.strip():
                base_indent = indent
            elif (
                indent <= base_indent
                and line.strip()
                and not line.strip().startswith("calculationItem")
            ):
                break

            line_content = line.strip()

            if line_content.startswith("precedence:"):
                calc_group["precedence"] = int(self._parse_property_value(line_content))
            elif line_content.startswith("calculationItem "):
                calc_group["calculation_items"].append(self._parse_calculation_item())
                continue

            self._advance_line()

        return calc_group

    def _parse_calculation_item(self) -> Dict[str, Any]:
        """Parse calculation item."""
        line = self._get_current_line().strip()

        if " = " in line:
            # calculationItem Name = Expression (could be single line or start of multiline)
            # Split on the first " = " to get the name part properly
            prefix = "calculationItem"
            if not line.startswith(prefix):
                raise TMDLParseError(
                    "Invalid calculation item definition", self.current_line + 1
                )

            remainder = line[len(prefix) :].strip()
            if " = " not in remainder:
                raise TMDLParseError(
                    "Invalid calculation item definition", self.current_line + 1
                )

            name_part, expression_start = remainder.split(" = ", 1)
            name = name_part.strip()
            expression_start = expression_start.strip()

            # Remove quotes if present
            if (name.startswith("'") and name.endswith("'")) or (
                name.startswith('"') and name.endswith('"')
            ):
                name = name[1:-1]

            self._advance_line()

            # If expression_start is empty or whitespace, this is a multiline expression
            if not expression_start:
                expression = self._parse_multiline_expression()
            else:
                # Single line expression
                expression = expression_start
        else:
            # Multi-line expression without = on same line (shouldn't happen in valid TMDL)
            match = re.match(r"calculationItem\s+(.+)", line)
            if not match:
                raise TMDLParseError(
                    "Invalid calculation item definition", self.current_line + 1
                )

            name = match.group(1).strip()
            # Remove quotes if present
            if (name.startswith("'") and name.endswith("'")) or (
                name.startswith('"') and name.endswith('"')
            ):
                name = name[1:-1]

            self._advance_line()
            expression = self._parse_multiline_expression()

        return {"name": name, "expression": expression}

    def _parse_multiline_expression(self) -> str:
        """Parse multi-line expression (typically DAX)."""
        expression_lines = []
        base_indent = None
        found_content = False

        while self.current_line < len(self.lines):
            line = self._get_current_line()

            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None:
                # Find the first line with actual content to set base indent
                if line.strip():
                    base_indent = indent
                    found_content = True
            elif indent < base_indent and found_content:
                # We've moved back to a lower indentation level
                break

            # Remove the base indentation and add to expression
            if line.strip() and base_indent is not None:
                cleaned_line = (
                    line[base_indent:] if len(line) > base_indent else line.strip()
                )
                expression_lines.append(cleaned_line)

            self._advance_line()

        return "\n".join(expression_lines).strip()

    def _parse_hierarchy(self) -> Dict[str, Any]:
        """Parse hierarchy definition."""
        line = self._get_current_line().strip()
        match = re.match(r"hierarchy\s+(.+)", line)
        if not match:
            raise TMDLParseError("Invalid hierarchy definition", self.current_line + 1)

        hierarchy_name = match.group(1).strip()

        # Remove quotes if present
        if (hierarchy_name.startswith("'") and hierarchy_name.endswith("'")) or (
            hierarchy_name.startswith('"') and hierarchy_name.endswith('"')
        ):
            hierarchy_name = hierarchy_name[1:-1]

        self._advance_line()

        hierarchy = {
            "name": hierarchy_name,
            "lineage_tag": "",
            "levels": [],
            "annotations": [],
        }

        base_indent = None

        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None and line.strip():
                base_indent = indent
            elif (
                indent <= base_indent
                and line.strip()
                and not line.strip().startswith(("level", "annotation"))
            ):
                break

            line_content = line.strip()

            if line_content.startswith("lineageTag:"):
                hierarchy["lineage_tag"] = self._parse_property_value(line_content)
            elif line_content.startswith("level "):
                hierarchy["levels"].append(self._parse_hierarchy_level())
                continue
            elif line_content.startswith("annotation "):
                hierarchy["annotations"].append(self._parse_annotation())
                continue

            self._advance_line()

        return hierarchy

    def _parse_hierarchy_level(self) -> Dict[str, Any]:
        """Parse hierarchy level."""
        line = self._get_current_line().strip()
        match = re.match(r"level\s+(.+)", line)
        if not match:
            raise TMDLParseError(
                "Invalid hierarchy level definition", self.current_line + 1
            )

        level_name = match.group(1)
        self._advance_line()

        level = {"name": level_name, "lineage_tag": "", "column": ""}

        base_indent = None

        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None and line.strip():
                base_indent = indent
            elif indent <= base_indent and line.strip():
                break

            line_content = line.strip()

            if line_content.startswith("lineageTag:"):
                level["lineage_tag"] = self._parse_property_value(line_content)
            elif line_content.startswith("column:"):
                level["column"] = self._parse_property_value(line_content)

            self._advance_line()

        return level

    def _parse_partition(self) -> Dict[str, Any]:
        """Parse partition definition."""
        line = self._get_current_line().strip()

        if " = " in line:
            # partition Name = mode
            match = re.match(r"partition\s+(.+?)\s*=\s*(.+)", line)
            if not match:
                raise TMDLParseError(
                    "Invalid partition definition", self.current_line + 1
                )

            partition_name = match.group(1).strip()
            mode = match.group(2).strip()
        else:
            # partition Name
            match = re.match(r"partition\s+(.+)", line)
            if not match:
                raise TMDLParseError(
                    "Invalid partition definition", self.current_line + 1
                )

            partition_name = match.group(1).strip()
            mode = "import"  # default

        self._advance_line()

        partition = {"name": partition_name, "mode": mode, "source": ""}

        base_indent = None

        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None and line.strip():
                base_indent = indent
            elif (
                indent <= base_indent
                and line.strip()
                and not line.strip().startswith("source")
            ):
                break

            line_content = line.strip()

            if line_content.startswith("mode:"):
                partition["mode"] = self._parse_property_value(line_content)
            elif line_content.startswith("source"):
                partition["source"] = self._parse_source()
                break

            self._advance_line()

        return partition

    def _parse_source(self) -> str:
        """Parse partition source (M query or DAX)."""
        line = self._get_current_line().strip()

        if line.startswith("source ="):
            # Single line source
            return line.replace("source =", "").strip()
        elif line.startswith("source"):
            # Multi-line source
            self._advance_line()
            return self._parse_multiline_expression()

        return ""

    def _parse_variation(self) -> Dict[str, Any]:
        """Parse column variation."""
        line = self._get_current_line().strip()
        match = re.match(r"variation\s+(.+)", line)
        if not match:
            raise TMDLParseError("Invalid variation definition", self.current_line + 1)

        variation_name = match.group(1)
        self._advance_line()

        variation = {"name": variation_name, "is_default": False}

        base_indent = None

        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None and line.strip():
                base_indent = indent
            elif indent <= base_indent and line.strip():
                break

            line_content = line.strip()

            if line_content.startswith("isDefault"):
                variation["is_default"] = True
            elif line_content.startswith("relationship:"):
                variation["relationship"] = self._parse_property_value(line_content)
            elif line_content.startswith("defaultHierarchy:"):
                variation["default_hierarchy"] = self._parse_property_value(
                    line_content
                )

            self._advance_line()

        return variation

    def _parse_culture_info(self) -> Dict[str, Any]:
        """Parse culture info definition."""
        line = self._get_current_line().strip()
        match = re.match(r"cultureInfo\s+(.+)", line)
        if not match:
            raise TMDLParseError(
                "Invalid culture info definition", self.current_line + 1
            )

        culture_name = match.group(1)
        self._advance_line()

        culture = {"name": culture_name}

        base_indent = None

        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None and line.strip():
                base_indent = indent
            elif indent <= 0:
                break

            line_content = line.strip()

            if line_content.startswith("linguisticMetadata"):
                culture["linguistic_metadata"] = self._parse_linguistic_metadata()
                continue
            elif line_content.startswith("contentType:"):
                culture["content_type"] = self._parse_property_value(line_content)

            self._advance_line()

        return culture

    def _parse_linguistic_metadata(self) -> Dict[str, Any]:
        """Parse linguistic metadata."""
        self._advance_line()  # Skip the linguisticMetadata line
        return self._parse_json_block()

    def _parse_json_block(self) -> Dict[str, Any]:
        """Parse a JSON block."""
        json_lines = []
        base_indent = None

        while self.current_line < len(self.lines):
            line = self._get_current_line()

            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None:
                base_indent = indent
            elif indent < base_indent:
                break

            json_lines.append(line.strip())
            self._advance_line()

        try:
            import json

            json_str = "\n".join(json_lines)
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {}

    def _parse_database(self) -> Dict[str, Any]:
        """Parse database definition."""
        self._advance_line()  # Skip the "database" line

        database = {}

        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)
            if indent <= 0:
                break

            line_content = line.strip()

            if line_content.startswith("compatibilityLevel:"):
                database["compatibility_level"] = int(
                    self._parse_property_value(line_content)
                )

            self._advance_line()

        return database

    def _parse_data_access_options(self) -> Dict[str, Any]:
        """Parse data access options."""
        self._advance_line()  # Skip the dataAccessOptions line

        options = {}
        base_indent = None

        while self.current_line < len(self.lines):
            line = self._get_current_line()
            if not line.strip():
                self._advance_line()
                continue

            indent = self._get_indentation(line)

            if base_indent is None:
                base_indent = indent
            elif indent < base_indent:
                break

            line_content = line.strip()

            if line_content == "legacyRedirects":
                options["legacy_redirects"] = True
            elif line_content == "returnErrorValuesAsNull":
                options["return_error_values_as_null"] = True

            self._advance_line()

        return options

    def _parse_property_value(self, line: str) -> str:
        """Parse property value from line like 'property: value'."""
        if ":" in line:
            value = line.split(":", 1)[1].strip()
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                return value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                return value[1:-1]
            return value
        return ""
