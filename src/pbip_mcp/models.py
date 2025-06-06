"""Pydantic data models for PBIP project components."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class DataType(str, Enum):
    """Column data types supported in TMDL."""

    STRING = "string"
    INT64 = "int64"
    DOUBLE = "double"
    BOOLEAN = "boolean"
    DATETIME = "dateTime"
    BINARY = "binary"


class SummarizeBy(str, Enum):
    """Column summarization types."""

    NONE = "none"
    SUM = "sum"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    AVERAGE = "average"


class PartitionMode(str, Enum):
    """Partition mode types."""

    IMPORT = "import"
    DIRECT_QUERY = "directQuery"
    DUAL = "dual"
    CALCULATED = "calculated"


class Cardinality(str, Enum):
    """Relationship cardinality types."""

    ONE_TO_MANY = "OneToMany"
    MANY_TO_ONE = "ManyToOne"
    ONE_TO_ONE = "OneToOne"
    MANY_TO_MANY = "ManyToMany"


class CrossFilteringBehavior(str, Enum):
    """Cross-filtering behavior for relationships."""

    AUTOMATIC = "Automatic"
    ONE_DIRECTION = "OneDirection"
    BOTH_DIRECTIONS = "BothDirections"


class Annotation(BaseModel):
    """TMDL annotation key-value pair."""

    name: str
    value: Union[str, int, float, bool, Dict[str, Any]]

    def __str__(self) -> str:
        if isinstance(self.value, str):
            return f'annotation {self.name} = "{self.value}"'
        elif isinstance(self.value, dict):
            import json

            return f"annotation {self.name} = {json.dumps(self.value)}"
        else:
            return f"annotation {self.name} = {self.value}"


class Column(BaseModel):
    """TMDL table column definition."""

    name: str
    data_type: DataType
    lineage_tag: str
    summarize_by: SummarizeBy = SummarizeBy.NONE
    source_column: Optional[str] = None
    format_string: Optional[str] = None
    is_hidden: bool = False
    is_name_inferred: bool = False
    data_category: Optional[str] = None
    sort_by_column: Optional[str] = None
    expression: Optional[str] = None  # For calculated columns
    description: Optional[str] = None
    annotations: List[Annotation] = Field(default_factory=list)


class Measure(BaseModel):
    """TMDL measure definition."""

    name: str
    expression: str
    lineage_tag: str
    format_string: Optional[str] = None
    is_hidden: bool = False
    description: Optional[str] = None
    annotations: List[Annotation] = Field(default_factory=list)


class CalculationItem(BaseModel):
    """TMDL calculation group item."""

    name: str
    expression: str


class CalculationGroup(BaseModel):
    """TMDL calculation group definition."""

    precedence: Optional[int] = None
    calculation_items: List[CalculationItem] = Field(default_factory=list)


class HierarchyLevel(BaseModel):
    """TMDL hierarchy level definition."""

    name: str
    lineage_tag: str
    column: str


class Hierarchy(BaseModel):
    """TMDL hierarchy definition."""

    name: str
    lineage_tag: str
    levels: List[HierarchyLevel] = Field(default_factory=list)
    annotations: List[Annotation] = Field(default_factory=list)


class Variation(BaseModel):
    """TMDL column variation definition."""

    is_default: bool = False
    relationship: Optional[str] = None
    default_hierarchy: Optional[str] = None


class Partition(BaseModel):
    """TMDL table partition definition."""

    name: str
    mode: PartitionMode
    source: str  # M query or DAX expression


class Table(BaseModel):
    """TMDL table definition."""

    name: str
    lineage_tag: str
    columns: List[Column] = Field(default_factory=list)
    measures: List[Measure] = Field(default_factory=list)
    hierarchies: List[Hierarchy] = Field(default_factory=list)
    partitions: List[Partition] = Field(default_factory=list)
    calculation_group: Optional[CalculationGroup] = None
    is_hidden: bool = False
    is_private: bool = False
    show_as_variations_only: bool = False
    description: Optional[str] = None
    annotations: List[Annotation] = Field(default_factory=list)


class Relationship(BaseModel):
    """TMDL relationship definition."""

    name: str
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cardinality: Optional[Cardinality] = None
    cross_filtering_behavior: Optional[CrossFilteringBehavior] = None
    is_active: bool = True
    join_on_date_behavior: Optional[str] = None


class CultureInfo(BaseModel):
    """TMDL culture information."""

    name: str
    linguistic_metadata: Optional[Dict[str, Any]] = None
    content_type: Optional[str] = None


class Database(BaseModel):
    """TMDL database configuration."""

    compatibility_level: int


class SemanticModel(BaseModel):
    """TMDL semantic model definition."""

    name: str
    culture: str
    default_power_bi_data_source_version: Optional[str] = None
    discourage_implicit_measures: bool = False
    source_query_culture: Optional[str] = None
    data_access_options: Optional[Dict[str, Any]] = None
    compatibility_level: Optional[int] = None

    tables: List[Table] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    culture_infos: List[CultureInfo] = Field(default_factory=list)
    annotations: List[Annotation] = Field(default_factory=list)


class ProjectReference(BaseModel):
    """PBIP project reference."""

    path: str
    type: Optional[str] = None  # "report" or "semanticModel" - optional


class ProjectArtifact(BaseModel):
    """PBIP project artifact definition."""

    report: Optional[ProjectReference] = None
    semantic_model: Optional[ProjectReference] = None


class ProjectSettings(BaseModel):
    """PBIP project settings."""

    enable_auto_recovery: bool = True


class ProjectInfo(BaseModel):
    """PBIP project root definition."""

    version: str
    artifacts: List[ProjectArtifact] = Field(default_factory=list)
    settings: ProjectSettings = Field(default_factory=ProjectSettings)


class PlatformMetadata(BaseModel):
    """Platform metadata for PBIP components."""

    type: str
    display_name: str


class PlatformConfig(BaseModel):
    """Platform configuration."""

    version: str
    logical_id: str


class Platform(BaseModel):
    """Platform definition file."""

    schema_url: str = Field(alias="$schema")
    metadata: PlatformMetadata
    config: PlatformConfig


class ProjectStructure(BaseModel):
    """Complete PBIP project structure."""

    project_info: ProjectInfo
    semantic_model: Optional[SemanticModel] = None
    platform_configs: Dict[str, Platform] = Field(default_factory=dict)
    editor_settings: Optional[Dict[str, Any]] = None
    diagram_layout: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic config."""

        populate_by_name = True
