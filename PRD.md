# Product Requirements Document: Power BI Project MCP Server

## 1. Executive Summary

### 1.1 Product Overview
The Power BI Project MCP (Model Context Protocol) Server is a specialized server implementation that enables local editing and manipulation of Power BI Desktop Project (.pbip) files through a standardized protocol interface. This server bridges the gap between AI-powered development tools and Power BI's native project format, enabling seamless semantic model and report editing capabilities.

### 1.2 Business Objectives
- Enable programmatic editing of Power BI Desktop Projects through MCP protocol
- Provide AI assistants and development tools with native PBIP file manipulation capabilities
- Streamline Power BI development workflows by enabling automated model and report modifications
- Support enterprise-grade Power BI development practices with proper version control integration

### 1.3 Target Users
- **AI Development Assistants**: Tools requiring PBIP file manipulation capabilities
- **Power BI Developers**: Professional developers working with PBIP projects
- **DevOps Engineers**: Teams implementing CI/CD pipelines for Power BI projects
- **Business Intelligence Teams**: Organizations adopting modern BI development practices

## 2. Product Vision

Create a robust, secure, and efficient MCP server that enables comprehensive manipulation of Power BI Desktop Projects, supporting both semantic model and report editing operations while maintaining file integrity and version control compatibility.

## 3. Technical Architecture

### 3.1 Core Technologies
- **Protocol**: Model Context Protocol (MCP)
- **Runtime**: Python 3.11+
- **Package Manager**: Astral's uv for fast dependency management
- **MCP Framework**: Python MCP SDK (`mcp` package)
- **File Processing**: Native file system operations with JSON/TMDL parsing
- **JSON Processing**: `json` and `jsonschema` libraries
- **Text Processing**: `pathlib`, `re`, and custom TMDL parsers
- **Validation**: Schema validation for PBIP file formats using `pydantic`
- **Security**: Sandboxed file operations with configurable access controls
- **Async Support**: `asyncio` for concurrent operations
- **Testing**: Comprehensive test suite with `pytest` and coverage reporting

### 3.2 Development Toolchain
- **Package Management**: `uv` for ultra-fast Python package installation and resolution
- **Project Configuration**: `pyproject.toml` for unified project configuration
- **Code Quality**: `ruff` for linting and formatting
- **Type Checking**: `mypy` for static type analysis
- **Testing**: `pytest` with async support and coverage reporting
- **Documentation**: `sphinx` with automated API documentation

### 3.3 PBIP File Structure Support

Based on the analysis of existing PBIP projects, the server must support the following file structure:

**Root Level:**
- `ProjectName.pbip` - Root project definition file

**Semantic Model Directory (`ProjectName.SemanticModel/`):**
- `definition.pbism` - Semantic model metadata
- `definition/model.tmdl` - Main model definition (TMDL format)
- `definition/tables/TableName.tmdl` - Individual table definitions
- `definition/cultures/` - Localization settings
- `.pbi/editorSettings.json` - Editor configuration
- `.pbi/cache.abf` - Binary cache files
- `diagramLayout.json` - Model diagram layout
- `.platform` - Platform metadata

**Report Directory (`ProjectName.Report/`):**
- `definition.pbir` - Report metadata
- `definition/pages/{pageId}/` - Individual page definitions
- `definition/pages/{pageId}/visuals/` - Visual definitions
- `StaticResources/` - Images, themes, etc.
- `.pbi/` - Report-specific settings

## 4. Functional Requirements

### 4.1 Core MCP Operations

#### 4.1.1 Resource Discovery
- **FR-001**: List available PBIP projects in specified directories
- **FR-002**: Enumerate semantic model components (tables, measures, relationships)
- **FR-003**: Discover report components (pages, visuals, layouts)
- **FR-004**: Provide project metadata and version information

#### 4.1.2 File System Operations
- **FR-005**: Read PBIP project structure and metadata
- **FR-006**: Parse and validate TMDL files for semantic models
- **FR-007**: Read and interpret JSON configuration files
- **FR-008**: Access report definition files and visual layouts

#### 4.1.3 Content Manipulation
- **FR-009**: Modify semantic model definitions (tables, columns, measures)
- **FR-010**: Update table relationships and hierarchies
- **FR-011**: Add, modify, or remove DAX measures and calculated columns
- **FR-012**: Update data source configurations and partitions
- **FR-013**: Modify report layouts and visual configurations
- **FR-014**: Update report themes and styling

### 4.2 Semantic Model Operations

#### 4.2.1 Table Management
- **FR-015**: Create new table definitions with proper TMDL syntax
- **FR-016**: Modify existing table schemas and properties
- **FR-017**: Update column data types, formats, and summarization settings
- **FR-018**: Manage table partitions and data source queries

#### 4.2.2 Measure and Calculation Management
- **FR-019**: Add DAX measures with proper formatting and annotations
- **FR-020**: Update calculated columns and calculated tables
- **FR-021**: Manage calculation groups and calculation items
- **FR-022**: Validate DAX syntax and dependencies

#### 4.2.3 Relationship Management
- **FR-023**: Create and modify table relationships
- **FR-024**: Update relationship properties (cardinality, filter direction)
- **FR-025**: Manage hierarchies and levels
- **FR-026**: Handle date table templates and auto-generated relationships

### 4.3 Report Operations

#### 4.3.1 Page Management
- **FR-027**: Create new report pages with layouts
- **FR-028**: Modify page properties and configurations
- **FR-029**: Update page-level filters and slicers
- **FR-030**: Manage page themes and styling

#### 4.3.2 Visual Management
- **FR-031**: Add new visuals to report pages
- **FR-032**: Modify visual properties and data bindings
- **FR-033**: Update visual formatting and styling
- **FR-034**: Configure visual interactions and drill-through

### 4.4 Validation and Integrity

#### 4.4.1 File Validation
- **FR-035**: Validate TMDL syntax and structure
- **FR-036**: Check JSON schema compliance for configuration files
- **FR-037**: Verify relationship consistency and referential integrity
- **FR-038**: Validate DAX expressions and measure dependencies

#### 4.4.2 Project Integrity
- **FR-039**: Maintain lineage tags and object identifiers
- **FR-040**: Preserve version information and annotations
- **FR-041**: Handle file dependencies and cross-references
- **FR-042**: Validate project structure completeness

## 5. Non-Functional Requirements

### 5.1 Performance
- **NFR-001**: Process PBIP files up to 100MB within 5 seconds
- **NFR-002**: Support concurrent operations on multiple projects using asyncio
- **NFR-003**: Minimize memory footprint for large semantic models
- **NFR-004**: Provide streaming responses for large file operations

### 5.2 Reliability
- **NFR-005**: Maintain 99.9% uptime for server operations
- **NFR-006**: Implement atomic operations to prevent file corruption
- **NFR-007**: Provide rollback capabilities for failed operations
- **NFR-008**: Handle graceful degradation during resource constraints

### 5.3 Security
- **NFR-009**: Implement configurable file system access controls
- **NFR-010**: Validate all input to prevent injection attacks using pydantic
- **NFR-011**: Provide audit logging for all file modifications
- **NFR-012**: Support read-only modes for sensitive environments

### 5.4 Compatibility
- **NFR-013**: Support PBIP format versions 1.0 through current
- **NFR-014**: Maintain compatibility with Power BI Desktop versions 2.120+
- **NFR-015**: Support Windows, macOS, and Linux operating systems
- **NFR-016**: Integrate with Git and other version control systems

## 6. API Specification

### 6.1 Python MCP Tools Implementation

#### 6.1.1 Project Management Tools

```python
from mcp.server import Server
from mcp.types import Tool, TextContent
from typing import List, Dict, Any
import asyncio

class PBIPProjectManager:
    
    @staticmethod
    async def list_pbip_projects(directory: str) -> List[Dict[str, Any]]:
        """List available PBIP projects in specified directory."""
        pass
    
    @staticmethod
    async def load_pbip_project(project_path: str) -> Dict[str, Any]:
        """Load complete project structure."""
        pass
    
    @staticmethod
    async def validate_pbip_project(project_path: str) -> Dict[str, Any]:
        """Validate project integrity and return validation results."""
        pass

# MCP Tool registration
app = Server("pbip-mcp-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="list_pbip_projects",
            description="List available PBIP projects in a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory path to scan"}
                },
                "required": ["directory"]
            }
        ),
        Tool(
            name="load_pbip_project",
            description="Load PBIP project structure and metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "description": "Path to .pbip file"}
                },
                "required": ["project_path"]
            }
        )
    ]
```

#### 6.1.2 Semantic Model Tools

```python
class SemanticModelManager:
    
    @staticmethod
    async def read_semantic_model(project_path: str) -> Dict[str, Any]:
        """Read complete semantic model definition."""
        pass
    
    @staticmethod
    async def update_model_metadata(
        project_path: str, 
        metadata: Dict[str, Any]
    ) -> None:
        """Update model metadata and annotations."""
        pass
    
    @staticmethod
    async def upsert_table(
        project_path: str,
        table_name: str,
        table_definition: Dict[str, Any]
    ) -> None:
        """Add or update table definition."""
        pass
    
    @staticmethod
    async def upsert_measure(
        project_path: str,
        table_name: str,
        measure_name: str,
        dax_expression: str,
        properties: Dict[str, Any] = None
    ) -> None:
        """Add or update DAX measure."""
        pass
    
    @staticmethod
    async def update_relationships(
        project_path: str,
        relationships: List[Dict[str, Any]]
    ) -> None:
        """Update table relationships."""
        pass
```

#### 6.1.3 Report Tools

```python
class ReportManager:
    
    @staticmethod
    async def read_report(project_path: str) -> Dict[str, Any]:
        """Read complete report definition."""
        pass
    
    @staticmethod
    async def upsert_report_page(
        project_path: str,
        page_id: str,
        page_definition: Dict[str, Any]
    ) -> None:
        """Add or update report page."""
        pass
    
    @staticmethod
    async def upsert_visual(
        project_path: str,
        page_id: str,
        visual_id: str,
        visual_definition: Dict[str, Any]
    ) -> None:
        """Add or update visual on a report page."""
        pass
    
    @staticmethod
    async def update_report_metadata(
        project_path: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Update report metadata and settings."""
        pass
```

#### 6.1.4 Utility Tools

```python
class UtilityManager:
    
    @staticmethod
    async def format_tmdl(content: str) -> str:
        """Format TMDL content with proper indentation and syntax."""
        pass
    
    @staticmethod
    async def validate_dax(
        expression: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate DAX expression syntax and dependencies."""
        pass
    
    @staticmethod
    def generate_lineage_tag() -> str:
        """Generate unique lineage tag for new objects."""
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    async def backup_project(
        project_path: str,
        backup_path: str
    ) -> None:
        """Create backup copy of PBIP project."""
        pass
```

### 6.2 MCP Resources

#### 6.2.1 Resource URI Scheme

```python
from mcp.types import Resource

class ResourceManager:
    
    @staticmethod
    async def get_resource(uri: str) -> Resource:
        """Get resource content by URI."""
        
        # Resource URI patterns:
        # pbip://project/{project_path}/overview
        # pbip://project/{project_path}/model
        # pbip://project/{project_path}/report
        # pbip://project/{project_path}/model/tables/{table_name}
        # pbip://project/{project_path}/model/tables/{table_name}/measures/{measure_name}
        # pbip://project/{project_path}/report/pages/{page_id}
        # pbip://project/{project_path}/report/pages/{page_id}/visuals/{visual_id}
        
        pass

@app.list_resources()
async def list_resources() -> List[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="pbip://project/*/overview",
            name="Project Overview",
            description="High-level project information and structure"
        ),
        Resource(
            uri="pbip://project/*/model",
            name="Semantic Model",
            description="Complete semantic model definition"
        ),
        Resource(
            uri="pbip://project/*/report",
            name="Report Definition",
            description="Complete report structure and visuals"
        )
    ]
```

## 7. Data Models

### 7.1 Pydantic Data Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ProjectInfo(BaseModel):
    name: str
    path: str
    version: str
    last_modified: datetime
    has_semantic_model: bool
    has_report: bool

class DataType(str, Enum):
    STRING = "string"
    INT64 = "int64"
    DOUBLE = "double"
    BOOLEAN = "boolean"
    DATETIME = "dateTime"
    BINARY = "binary"

class SummarizeBy(str, Enum):
    NONE = "none"
    SUM = "sum"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    AVERAGE = "average"

class Annotation(BaseModel):
    name: str
    value: Any

class Column(BaseModel):
    name: str
    data_type: DataType
    lineage_tag: str
    summarize_by: SummarizeBy
    source_column: Optional[str] = None
    format_string: Optional[str] = None
    annotations: List[Annotation] = Field(default_factory=list)

class Measure(BaseModel):
    name: str
    expression: str
    format_string: Optional[str] = None
    lineage_tag: str
    annotations: List[Annotation] = Field(default_factory=list)

class Partition(BaseModel):
    name: str
    mode: str  # "import", "directQuery", "dual"
    source: str  # M query or SQL

class Table(BaseModel):
    name: str
    lineage_tag: str
    columns: List[Column] = Field(default_factory=list)
    measures: List[Measure] = Field(default_factory=list)
    partitions: List[Partition] = Field(default_factory=list)
    annotations: List[Annotation] = Field(default_factory=list)

class Relationship(BaseModel):
    name: str
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cardinality: str  # "OneToMany", "ManyToOne", "OneToOne", "ManyToMany"
    cross_filtering_behavior: str  # "Automatic", "OneDirection", "BothDirections"
    is_active: bool = True

class SemanticModel(BaseModel):
    version: str
    culture: str
    tables: List[Table] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    annotations: List[Annotation] = Field(default_factory=list)

class Visual(BaseModel):
    id: str
    type: str
    title: Optional[str] = None
    x: float
    y: float
    width: float
    height: float
    config: Dict[str, Any] = Field(default_factory=dict)

class ReportPage(BaseModel):
    id: str
    name: str
    visuals: List[Visual] = Field(default_factory=list)
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    width: float = 1280
    height: float = 720

class ReportDefinition(BaseModel):
    version: str
    pages: List[ReportPage] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProjectStructure(BaseModel):
    info: ProjectInfo
    semantic_model: Optional[SemanticModel] = None
    report: Optional[ReportDefinition] = None
```

## 8. Implementation Phases

### Phase 1: Core Infrastructure (Weeks 1-3)
- **Week 1**: Python MCP server framework setup using `uv` and `pyproject.toml`
  - Project initialization with `uv init`
  - Configure `pyproject.toml` with dependencies and dev tools
  - Set up basic MCP server structure
  - Implement basic logging and configuration
- **Week 2**: File system operations and project discovery
  - PBIP project discovery and loading with `pathlib`
  - JSON parsing and Pydantic model validation
  - Basic error handling and validation
- **Week 3**: TMDL parsing infrastructure
  - Basic TMDL file parsing capabilities
  - Unit tests for core functionality
  - Initial CI/CD setup with testing

### Phase 2: Semantic Model Operations (Weeks 4-7)
- **Week 4**: Table definition operations
  - Table reading and writing with TMDL format
  - Column management operations
  - Unit tests for table operations
- **Week 5**: Measure management
  - DAX measure creation and modification
  - Measure validation and formatting
  - Integration tests for measure operations
- **Week 6**: Relationship management
  - Relationship creation and modification
  - Hierarchy management
  - Comprehensive testing for relationship logic
- **Week 7**: TMDL formatting and validation
  - TMDL syntax validation
  - Lineage tag management
  - Performance optimization and testing

### Phase 3: Report Operations (Weeks 8-10)
- **Week 8**: Report structure manipulation
  - Report definition reading and writing
  - Page management operations
  - Unit tests for report operations
- **Week 9**: Visual management
  - Visual definition management
  - Layout operations
  - Integration tests for visual operations
- **Week 10**: Static resources and styling
  - Theme and resource handling
  - JSON schema validation for report components
  - End-to-end testing for report features

### Phase 4: Advanced Features (Weeks 11-13)
- **Week 11**: Validation and integrity
  - DAX validation utilities
  - Project integrity validation
  - Comprehensive validation testing
- **Week 12**: Performance and monitoring
  - Async performance optimizations
  - File system monitoring with `watchdog`
  - Load testing and benchmarking
- **Week 13**: Backup and recovery
  - Backup and restore operations
  - Error recovery mechanisms
  - Stress testing and reliability validation

### Phase 5: Testing and Documentation (Weeks 14-16)
- **Week 14**: Comprehensive testing suite
  - Unit test completion (target: >95% coverage)
  - Integration test suite
  - End-to-end testing scenarios
- **Week 15**: Performance and security testing
  - Performance benchmarking
  - Security testing and validation
  - Load testing with concurrent operations
- **Week 16**: Documentation and examples
  - API documentation with `sphinx`
  - Example implementations and tutorials
  - CLI interface with `click`
  - User guides and developer documentation

## 9. Development Environment Setup

### 9.1 Project Structure

**Modern Python Project Structure:**
- `src/pbip_mcp/` - Main package directory
  - `__init__.py` - Package initialization
  - `server.py` - Main MCP server implementation
  - `models.py` - Pydantic data models
- `src/pbip_mcp/parsers/` - File parsing modules
  - `tmdl_parser.py` - TMDL file parser
  - `json_parser.py` - JSON configuration parser
  - `project_parser.py` - Main project parser
- `src/pbip_mcp/managers/` - Business logic managers
  - `project_manager.py` - Project-level operations
  - `semantic_model_manager.py` - Model operations
  - `report_manager.py` - Report operations
  - `utility_manager.py` - Utility functions
- `src/pbip_mcp/validators/` - Validation modules
  - `tmdl_validator.py` - TMDL syntax validation
  - `dax_validator.py` - DAX expression validation
  - `project_validator.py` - Project integrity validation
- `tests/` - Comprehensive test suite
  - `unit/` - Unit tests
  - `integration/` - Integration tests
  - `fixtures/` - Test data and fixtures
  - `conftest.py` - Pytest configuration
- `docs/` - Documentation source
- `pyproject.toml` - Project configuration and dependencies
- `README.md` - Project documentation
- `.github/workflows/` - CI/CD workflows

### 9.2 Installation and Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <repository-url>
cd pbip-mcp-server

# Create virtual environment and install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
uv pip install -e .

# Run the MCP server
uv run python -m pbip_mcp.server

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=pbip_mcp --cov-report=html

# Format code
uv run ruff format

# Lint code
uv run ruff check

# Type check
uv run mypy src/pbip_mcp
```

### 9.3 pyproject.toml Configuration

```toml
[project]
name = "pbip-mcp-server"
version = "0.1.0"
description = "Power BI Project MCP Server for local editing of PBIP files"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
keywords = ["powerbi", "mcp", "pbip", "business-intelligence"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    # Core MCP and validation
    "mcp>=0.1.0",
    "pydantic>=2.0.0",
    "jsonschema>=4.0.0",
    
    # File processing and utilities
    "charset-normalizer>=3.0.0",
    "python-dateutil>=2.8.0",
    
    # Optional features
    "watchdog>=3.0.0",
    "click>=8.0.0",
    "structlog>=23.0.0",
]

[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "pytest-xdist>=3.0.0",  # Parallel testing
    
    # Code quality
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
    
    # Documentation
    "sphinx>=7.0.0",
    "sphinx-rtd-theme>=1.3.0",
    "sphinx-autodoc-typehints>=1.20.0",
]

test = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
]

docs = [
    "sphinx>=7.0.0",
    "sphinx-rtd-theme>=1.3.0",
    "sphinx-autodoc-typehints>=1.20.0",
]

[project.scripts]
pbip-mcp = "pbip_mcp.cli:main"

[project.urls]
Homepage = "https://github.com/your-org/pbip-mcp-server"
Documentation = "https://pbip-mcp-server.readthedocs.io/"
Repository = "https://github.com/your-org/pbip-mcp-server.git"
Issues = "https://github.com/your-org/pbip-mcp-server/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/pbip_mcp"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=pbip_mcp",
    "--cov-branch",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src/pbip_mcp"]
omit = [
    "tests/*",
    "src/pbip_mcp/__main__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]

[tool.ruff]
target-version = "py39"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by formatter
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.per-file-ignores]
"tests/**/*" = ["F401", "F811"]

[tool.mypy]
python_version = "3.11"
check_untyped_defs = true
disallow_any_generics = true
disallow_incomplete_defs = true
disallow_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_return_any = true
strict_equality = true

[[tool.mypy.overrides]]
module = [
    "mcp.*",
    "watchdog.*",
]
ignore_missing_imports = true
```

## 10. Testing Strategy

### 10.1 Test Architecture

#### 10.1.1 Test Categories
- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test complete workflows from MCP client to file system
- **Performance Tests**: Validate performance requirements
- **Security Tests**: Verify security controls and input validation

#### 10.1.2 Test Structure
