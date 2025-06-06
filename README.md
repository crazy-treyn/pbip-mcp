# pbip-mcp (Power BI Project MCP Server)
## Purpose
An easy and simple way to interact with Power BI Projects via MCP Clients to improve productivity of typical semantic model development tasks.
## Installation
### Prerequisites:
- `uv`
- Power BI Project using .TMDL format (will not work with .TMSL)
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

### Project Management
- **`list_projects`** - List all PBIP projects in a directory
  - Parameters: `directory` (required)
- **`load_project`** - Load complete PBIP project structure and metadata
  - Parameters: `project_path` (required)

### Table Operations
- **`list_tables`** - List all tables in the project
  - Parameters: `project_path` (required)
- **`get_table_details`** - Get detailed information about a table
  - Parameters: `project_path` (required), `table_name` (required)

### Column Operations
- **`list_columns`** - List all columns in a table
  - Parameters: `project_path` (required), `table_name` (required)
- **`add_column`** - Add a new column to a table
  - Parameters: `project_path`, `table_name`, `column_name` (required); `data_type`, `expression`, `format_string`, `summarize_by`, `is_hidden` (optional)
- **`update_column`** - Update an existing column
  - Parameters: `project_path`, `table_name`, `column_name` (required); `data_type`, `expression`, `format_string`, `summarize_by`, `is_hidden` (optional)
- **`delete_column`** - Delete a column from a table
  - Parameters: `project_path`, `table_name`, `column_name` (required)

### Measure Operations
- **`list_measures`** - List all measures in the project
  - Parameters: `project_path` (required), `table_name` (optional)
- **`add_measure`** - Add a new measure to a table
  - Parameters: `project_path`, `table_name`, `measure_name`, `expression` (required); `description`, `format_string` (optional)
- **`update_measure`** - Update an existing measure
  - Parameters: `project_path`, `table_name`, `measure_name` (required); `expression`, `description`, `format_string` (optional)
- **`delete_measure`** - Delete a measure from a table
  - Parameters: `project_path`, `table_name`, `measure_name` (required)

### Relationship Operations
- **`list_relationships`** - List all relationships in the project
  - Parameters: `project_path` (required)

## Usage
Once the MCP Client is setup and has connected to the MCP server, start off your converstaion by passing the full path of your PBIP project (the directory where the .pbip file is located) and ask your question
### Example Report
There is an example report provided for you to test with so you don't have to use your own, located in the `TestReport` folder
### Example questions
- List all the columns and measures in the table "Fact" in my Power BI Project here: {ADD_FULL_PATH_TO_PBI_PROJECT_DIRECTORY}
- Add descriptions to all measures without descriptions
- Add YTD variants of all my measures using the following date logic: {insert date logic here}

