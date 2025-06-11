# pbip-mcp (Power BI Project MCP Server)
## Purpose
An easy and simple way to interact with Power BI Projects and standalone Semantic Models via MCP Clients to improve productivity of typical semantic model development tasks.

**Supports both:**
- 📁 **PBIP Projects**: Directories containing a `.pbip` file with associated `.SemanticModel` folders
- 📂 **Standalone Semantic Models**: Individual `.SemanticModel` directories
## Installation
### Prerequisites:
- `uv`
- **Power BI Project** (directory with `.pbip` file) OR **Standalone Semantic Model** (`.SemanticModel` folder) using .TMDL format (will not work with .TMSL)
- MCP Client like VS Code or Claude Desktop

### Install MCP server
```bash
git clone https://github.com/crazy-treyn/pbip-mcp.git
cd pbip-mcp
uv sync # initialize virtual environment and install dependencies
```

### Add MCP server to MCP Client
```json
{
  "mcpServers": {
    "pbip-mcp": {
      "command": "C:\\{YOUR_GIT_REPO_HERE}\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "pbip_mcp.server"
      ]
    }
  }
}
```

## Available MCP Tools

### 📊 Tools Overview Matrix

| Category | Tool | Scope | Purpose | Efficiency |
|----------|------|-------|---------|------------|
| **Project** | `list_projects` | Directory | Find all PBIP projects | 🚀 Single call |
| **Project** | `load_project` | Single project | Load project metadata | 🚀 Single call |
| **Model** | `get_model_details` | Entire model | Complete model analysis | 🚀 Everything at once |
| **Tables** | `list_tables` | All tables | Basic table information | 🚀 Single call |
| **Tables** | `get_table_details` | Single table | Deep table analysis | ⚡ Per table |
| **Columns** | `list_columns` | All/Single table | Column information | 🚀 All tables OR ⚡ per table |
| **Columns** | `add_column` | Single table | Create new column | ⚡ Per column |
| **Columns** | `update_column` | Single table | Modify existing column | ⚡ Per column |
| **Columns** | `delete_column` | Single table | Remove column | ⚡ Per column |
| **Measures** | `list_measures` | All/Single table | Measure information | 🚀 All tables OR ⚡ per table |
| **Measures** | `add_measure` | Single table | Create new measure | ⚡ Per measure |
| **Measures** | `update_measure` | Single table | Modify existing measure | ⚡ Per measure |
| **Measures** | `delete_measure` | Single table | Remove measure | ⚡ Per measure |
| **Relationships** | `list_relationships` | All relationships | Relationship information | 🚀 Single call |

**Legend:** 🚀 = Bulk operations (high efficiency) | ⚡ = Single item operations

### 📋 Detailed Tool Reference

#### **Project Management**
| Tool | Required Parameters | Optional Parameters | Description |
|------|-------------------|-------------------|-------------|
| `list_projects` | `directory` | - | Scan directory for all PBIP projects and standalone semantic models |
| `load_project` | `project_path` | - | Load complete project structure with metadata and artifact information |

#### **Model Analysis**
| Tool | Required Parameters | Optional Parameters | Description |
|------|-------------------|-------------------|-------------|
| `get_model_details` | `project_path`* | - | **🚀 BULK:** Complete model overview with all tables, columns, measures, relationships, and statistics |

*`project_path` accepts either:
- Path to PBIP project directory (containing `.pbip` file)
- Path to standalone `.SemanticModel` directory

#### **Table Operations**
| Tool | Required Parameters | Optional Parameters | Description |
|------|-------------------|-------------------|-------------|
| `list_tables` | `project_path`* | - | Basic information for all tables (name, counts, visibility flags) |
| `get_table_details` | `project_path`*, `table_name` | - | Detailed single table analysis including columns, measures, partitions, hierarchies, and relationships |

#### **Column Operations**
| Tool | Required Parameters | Optional Parameters | Description |
|------|-------------------|-------------------|-------------|
| `list_columns` | `project_path`* | `table_name` | **🚀 BULK:** All columns across all tables OR single table columns with summary statistics |
| `add_column` | `project_path`*, `table_name`, `column_name` | `data_type`, `expression`, `format_string`, `summarize_by`, `is_hidden` | Create new regular or calculated column |
| `update_column` | `project_path`*, `table_name`, `column_name` | `data_type`, `expression`, `format_string`, `summarize_by`, `is_hidden` | Modify existing column properties |
| `delete_column` | `project_path`*, `table_name`, `column_name` | - | Remove column from table |

#### **Measure Operations**
| Tool | Required Parameters | Optional Parameters | Description |
|------|-------------------|-------------------|-------------|
| `list_measures` | `project_path`* | `table_name` | **🚀 BULK:** All measures across all tables OR single table measures with summary statistics |
| `add_measure` | `project_path`*, `table_name`, `measure_name`, `expression` | `description`, `format_string` | Create new DAX measure with validation |
| `update_measure` | `project_path`*, `table_name`, `measure_name` | `expression`, `description`, `format_string` | Modify existing measure properties |
| `delete_measure` | `project_path`*, `table_name`, `measure_name` | - | Remove measure from table |

#### **Relationship Operations**
| Tool | Required Parameters | Optional Parameters | Description |
|------|-------------------|-------------------|-------------|
| `list_relationships` | `project_path`* | - | All model relationships with cardinality, active status, and summary statistics |

> **Note:** All `project_path` parameters accept either:
> - Path to PBIP project directory (containing `.pbip` file)  
> - Path to standalone `.SemanticModel` directory

## Usage
Once the MCP Client is setup and has connected to the MCP server, start your conversation by providing the full path to either:
- **PBIP Project**: Path to the directory containing your `.pbip` file
- **Standalone Semantic Model**: Path directly to your `.SemanticModel` directory

### Supported Path Types
```bash
# PBIP Project (directory containing .pbip file)
C:\MyProject\SalesReport\

# Standalone Semantic Model (direct path to .SemanticModel folder)  
C:\MyProject\SalesReport.SemanticModel\
```

### Example Report
There is an example report provided for you to test with so you don't have to use your own, located in the `TestReport` folder

### Example Questions
**For PBIP Projects:**
- List all the columns and measures in the table "Fact" in my Power BI Project here: `C:\Projects\SalesAnalysis\`
- Get complete model details for: `C:\Users\YourName\PowerBI\MyProject\`

**For Standalone Semantic Models:**
- Analyze all tables and relationships in: `C:\Models\SalesData.SemanticModel\`
- Add descriptions to all measures without descriptions in: `C:\SemanticModels\Finance.SemanticModel\`

**General Tasks:**
- Add YTD variants of all my measures using the following date logic: {insert date logic here}
- Show me all calculated columns across all tables

