"""PBIP project parser for loading complete project structures."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import ProjectStructure, ProjectInfo, SemanticModel, Platform
from .tmdl_parser import TMDLParser, TMDLParseError


class ProjectParseError(Exception):
    """Error parsing PBIP project."""

    pass


class ProjectParser:
    """Parser for complete PBIP projects."""

    def __init__(self):
        self.tmdl_parser = TMDLParser()

    def load_project(self, project_path: str) -> ProjectStructure:
        """Load complete PBIP project from file path."""
        project_dir = Path(project_path)

        if not project_dir.exists():
            raise ProjectParseError(f"Project path does not exist: {project_path}")

        # Find the .pbip file
        pbip_file = None
        if project_dir.is_file() and project_dir.suffix == ".pbip":
            pbip_file = project_dir
            project_dir = project_dir.parent
        else:
            # Look for .pbip files in the directory
            pbip_files = list(project_dir.glob("*.pbip"))
            if not pbip_files:
                raise ProjectParseError(f"No .pbip file found in {project_path}")
            pbip_file = pbip_files[0]

        # Load project info from .pbip file
        project_info = self._load_project_info(pbip_file)

        # Load semantic model if present
        semantic_model = None
        semantic_model_dir = self._find_semantic_model_dir(project_dir, pbip_file.stem)
        if semantic_model_dir:
            semantic_model = self._load_semantic_model(semantic_model_dir)

        # Load platform configs
        platform_configs = self._load_platform_configs(project_dir)

        # Load editor settings
        editor_settings = self._load_editor_settings(semantic_model_dir)

        # Load diagram layout
        diagram_layout = self._load_diagram_layout(semantic_model_dir)

        return ProjectStructure(
            project_info=project_info,
            semantic_model=semantic_model,
            platform_configs=platform_configs,
            editor_settings=editor_settings,
            diagram_layout=diagram_layout,
        )

    def _load_project_info(self, pbip_file: Path) -> ProjectInfo:
        """Load project info from .pbip file."""
        try:
            with open(pbip_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return ProjectInfo(**data)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise ProjectParseError(f"Error loading project file {pbip_file}: {e}")

    def _find_semantic_model_dir(
        self, project_dir: Path, project_name: str
    ) -> Optional[Path]:
        """Find semantic model directory."""
        # Try common patterns
        possible_dirs = [
            project_dir / f"{project_name}.SemanticModel",
            project_dir / f"{project_name}.Dataset",
            project_dir / "SemanticModel",
            project_dir / "Dataset",
        ]

        for dir_path in possible_dirs:
            if dir_path.exists() and dir_path.is_dir():
                return dir_path

        # Look for any .SemanticModel directories
        semantic_dirs = list(project_dir.glob("*.SemanticModel"))
        if semantic_dirs:
            return semantic_dirs[0]

        return None

    def _load_semantic_model(self, semantic_model_dir: Path) -> Optional[SemanticModel]:
        """Load semantic model from directory."""
        try:
            definition_dir = semantic_model_dir / "definition"
            if not definition_dir.exists():
                return None

            # Load main model definition
            model_file = definition_dir / "model.tmdl"
            if not model_file.exists():
                return None

            with open(model_file, "r", encoding="utf-8") as f:
                model_content = f.read()

            model_data = self.tmdl_parser.parse_file(model_content)
            model_info = model_data.get("model", {})

            # Initialize semantic model
            semantic_model = SemanticModel(
                name=model_info.get("name", "Model"),
                culture=model_info.get("culture", "en-US"),
                default_power_bi_data_source_version=model_info.get(
                    "default_power_bi_data_source_version"
                ),
                discourage_implicit_measures=model_info.get(
                    "discourage_implicit_measures", False
                ),
                source_query_culture=model_info.get("source_query_culture"),
                data_access_options=model_info.get("data_access_options"),
            )

            # Load tables
            tables_dir = definition_dir / "tables"
            if tables_dir.exists():
                # If model has table refs, prioritize loading those tables
                table_refs = model_info.get("table_refs", [])
                loaded_tables = set()

                # Load referenced tables first
                for table_ref in table_refs:
                    table_file = tables_dir / f"{table_ref}.tmdl"
                    if table_file.exists():
                        table_data = self._load_table(table_file)
                        if table_data:
                            table_obj = self._convert_table_dict_to_model(table_data)
                            semantic_model.tables.append(table_obj)
                            loaded_tables.add(table_ref)

                # Load any remaining tables not in refs
                for table_file in tables_dir.glob("*.tmdl"):
                    table_name = table_file.stem
                    if table_name not in loaded_tables:
                        table_data = self._load_table(table_file)
                        if table_data:
                            table_obj = self._convert_table_dict_to_model(table_data)
                            semantic_model.tables.append(table_obj)

            # Load relationships
            relationships_file = definition_dir / "relationships.tmdl"
            if relationships_file.exists():
                relationships_data = self._load_relationships(relationships_file)
                for rel_data in relationships_data:
                    rel_obj = self._convert_relationship_dict_to_model(rel_data)
                    semantic_model.relationships.append(rel_obj)

            # Load cultures
            cultures_dir = definition_dir / "cultures"
            if cultures_dir.exists():
                for culture_file in cultures_dir.glob("*.tmdl"):
                    culture_data = self._load_culture(culture_file)
                    if culture_data:
                        culture_obj = self._convert_culture_dict_to_model(culture_data)
                        semantic_model.culture_infos.append(culture_obj)

            # Load database info
            database_file = definition_dir / "database.tmdl"
            if database_file.exists():
                database_data = self._load_database(database_file)
                if database_data and "compatibility_level" in database_data:
                    semantic_model.compatibility_level = database_data[
                        "compatibility_level"
                    ]

            # Add annotations from model
            for annotation_data in model_info.get("annotations", []):
                from ..models import Annotation

                annotation_obj = Annotation(
                    name=annotation_data.get("name", ""),
                    value=annotation_data.get("value", ""),
                )
                semantic_model.annotations.append(annotation_obj)

            return semantic_model

        except Exception as e:
            raise ProjectParseError(f"Error loading semantic model: {e}")

    def _load_table(self, table_file: Path) -> Optional[Dict[str, Any]]:
        """Load table definition from TMDL file."""
        try:
            with open(table_file, "r", encoding="utf-8") as f:
                content = f.read()

            parsed = self.tmdl_parser.parse_file(content)
            tables = parsed.get("tables", [])

            if tables:
                return tables[0]  # Should only be one table per file

            return None

        except Exception as e:
            print(f"Warning: Error loading table {table_file}: {e}")
            return None

    def _convert_table_dict_to_model(self, table_data: Dict[str, Any]):
        """Convert table dictionary to Pydantic model."""
        from ..models import (
            Table,
            Column,
            Measure,
            Hierarchy,
            Partition,
            CalculationGroup,
            Annotation,
        )

        # Convert columns
        columns = []
        for col_data in table_data.get("columns", []):
            columns.append(
                Column(
                    name=col_data.get("name", ""),
                    data_type=col_data.get("data_type", "string"),
                    lineage_tag=col_data.get("lineage_tag", ""),
                    summarize_by=col_data.get("summarize_by", "none"),
                    source_column=col_data.get("source_column"),
                    format_string=col_data.get("format_string"),
                    is_hidden=col_data.get("is_hidden", False),
                    is_name_inferred=col_data.get("is_name_inferred", False),
                    data_category=col_data.get("data_category"),
                    sort_by_column=col_data.get("sort_by_column"),
                    expression=col_data.get("expression"),
                    description=col_data.get("description"),
                    annotations=[
                        Annotation(name=ann.get("name", ""), value=ann.get("value", ""))
                        for ann in col_data.get("annotations", [])
                    ],
                )
            )

        # Convert measures
        measures = []
        for meas_data in table_data.get("measures", []):
            measures.append(
                Measure(
                    name=meas_data.get("name", ""),
                    expression=meas_data.get("expression", ""),
                    lineage_tag=meas_data.get("lineage_tag", ""),
                    format_string=meas_data.get("format_string"),
                    is_hidden=meas_data.get("is_hidden", False),
                    description=meas_data.get("description"),
                    annotations=[
                        Annotation(name=ann.get("name", ""), value=ann.get("value", ""))
                        for ann in meas_data.get("annotations", [])
                    ],
                )
            )

        # Convert hierarchies (simplified for now)
        hierarchies = []
        for hier_data in table_data.get("hierarchies", []):
            hierarchies.append(
                Hierarchy(
                    name=hier_data.get("name", ""),
                    lineage_tag=hier_data.get("lineage_tag", ""),
                    levels=[],  # TODO: Convert levels if needed
                    annotations=[
                        Annotation(name=ann.get("name", ""), value=ann.get("value", ""))
                        for ann in hier_data.get("annotations", [])
                    ],
                )
            )

        # Convert partitions (simplified for now)
        partitions = []
        for part_data in table_data.get("partitions", []):
            partitions.append(
                Partition(
                    name=part_data.get("name", ""),
                    mode=part_data.get("mode", "import"),
                    source=part_data.get("source", ""),
                )
            )

        # Convert annotations
        annotations = [
            Annotation(name=ann.get("name", ""), value=ann.get("value", ""))
            for ann in table_data.get("annotations", [])
        ]

        # Create table object
        table = Table(
            name=table_data.get("name", ""),
            lineage_tag=table_data.get("lineage_tag", ""),
            columns=columns,
            measures=measures,
            hierarchies=hierarchies,
            partitions=partitions,
            calculation_group=table_data.get(
                "calculation_group"
            ),  # TODO: Convert if needed
            is_hidden=table_data.get("is_hidden", False),
            is_private=table_data.get("is_private", False),
            show_as_variations_only=table_data.get("show_as_variations_only", False),
            description=table_data.get("description"),
            annotations=annotations,
        )

        return table

    def _convert_culture_dict_to_model(self, culture_data: Dict[str, Any]):
        """Convert culture dictionary to Pydantic model."""
        from ..models import CultureInfo

        return CultureInfo(
            name=culture_data.get("name", ""),
            linguistic_metadata=culture_data.get("linguistic_metadata"),
            content_type=culture_data.get("content_type"),
        )

    def _convert_relationship_dict_to_model(self, rel_data: Dict[str, Any]):
        """Convert relationship dictionary to Pydantic model."""
        from ..models import Relationship

        return Relationship(
            name=rel_data.get("name", ""),
            from_table=rel_data.get("from_table", ""),
            from_column=rel_data.get("from_column", ""),
            to_table=rel_data.get("to_table", ""),
            to_column=rel_data.get("to_column", ""),
            cardinality=rel_data.get("cardinality"),
            cross_filtering_behavior=rel_data.get("cross_filtering_behavior"),
            is_active=rel_data.get("is_active", True),
            join_on_date_behavior=rel_data.get("join_on_date_behavior"),
        )

    def _load_relationships(self, relationships_file: Path) -> List[Dict[str, Any]]:
        """Load relationships from TMDL file."""
        try:
            with open(relationships_file, "r", encoding="utf-8") as f:
                content = f.read()

            parsed = self.tmdl_parser.parse_file(content)
            return parsed.get("relationships", [])

        except Exception as e:
            print(f"Warning: Error loading relationships {relationships_file}: {e}")
            return []

    def _load_culture(self, culture_file: Path) -> Optional[Dict[str, Any]]:
        """Load culture info from TMDL file."""
        try:
            with open(culture_file, "r", encoding="utf-8") as f:
                content = f.read()

            parsed = self.tmdl_parser.parse_file(content)
            culture_infos = parsed.get("culture_infos", [])

            if culture_infos:
                return culture_infos[0]

            return None

        except Exception as e:
            print(f"Warning: Error loading culture {culture_file}: {e}")
            return None

    def _load_database(self, database_file: Path) -> Optional[Dict[str, Any]]:
        """Load database info from TMDL file."""
        try:
            with open(database_file, "r", encoding="utf-8") as f:
                content = f.read()

            parsed = self.tmdl_parser.parse_file(content)
            return parsed.get("database", {})

        except Exception as e:
            print(f"Warning: Error loading database {database_file}: {e}")
            return None

    def _load_platform_configs(self, project_dir: Path) -> Dict[str, Platform]:
        """Load platform configuration files."""
        platform_configs = {}

        # Look for .platform files
        for platform_file in project_dir.rglob(".platform"):
            try:
                with open(platform_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Get relative path for key
                rel_path = platform_file.relative_to(project_dir)
                key = str(rel_path.parent)

                platform_configs[key] = Platform(**data)

            except Exception as e:
                print(f"Warning: Error loading platform config {platform_file}: {e}")

        return platform_configs

    def _load_editor_settings(
        self, semantic_model_dir: Optional[Path]
    ) -> Optional[Dict[str, Any]]:
        """Load editor settings."""
        if not semantic_model_dir:
            return None

        settings_file = semantic_model_dir / ".pbi" / "editorSettings.json"
        if not settings_file.exists():
            return None

        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Error loading editor settings: {e}")
            return None

    def _load_diagram_layout(
        self, semantic_model_dir: Optional[Path]
    ) -> Optional[Dict[str, Any]]:
        """Load diagram layout."""
        if not semantic_model_dir:
            return None

        layout_file = semantic_model_dir / "diagramLayout.json"
        if not layout_file.exists():
            return None

        try:
            with open(layout_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Error loading diagram layout: {e}")
            return None

    def list_projects(self, directory: str) -> List[Dict[str, Any]]:
        """List all PBIP projects in a directory."""
        directory_path = Path(directory)

        if not directory_path.exists():
            raise ProjectParseError(f"Directory does not exist: {directory}")

        projects = []

        # Find all .pbip files
        for pbip_file in directory_path.rglob("*.pbip"):
            try:
                project_info = self._load_project_info(pbip_file)

                # Get basic project information
                project_data = {
                    "name": pbip_file.stem,
                    "path": str(pbip_file),
                    "version": project_info.version,
                    "has_semantic_model": False,
                    "has_report": False,
                }

                # Check for artifacts
                for artifact in project_info.artifacts:
                    if hasattr(artifact, "report") and artifact.report:
                        project_data["has_report"] = True
                    # Note: semantic model detection would need the artifact structure

                # Check for semantic model directory
                semantic_model_dir = self._find_semantic_model_dir(
                    pbip_file.parent, pbip_file.stem
                )
                if semantic_model_dir:
                    project_data["has_semantic_model"] = True

                projects.append(project_data)

            except Exception as e:
                print(f"Warning: Error processing project {pbip_file}: {e}")

        return projects
