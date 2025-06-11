"""Pytest configuration and fixtures for pbip-mcp tests."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

from pbip_mcp.parsers import ProjectParser
from pbip_mcp.writers import TMDLWriter
from pbip_mcp.operations import MeasureOperations, ColumnOperations, TableOperations, RelationshipOperations


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def standalone_semantic_model_path(temp_dir):
    """Create a copy of the standalone semantic model for testing."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "standalone_semantic_model"
    test_model_dir = temp_dir / "TestCalcGroups.SemanticModel"
    shutil.copytree(fixtures_dir / "TestCalcGroups.SemanticModel", test_model_dir)
    return test_model_dir


@pytest.fixture
def pbip_project_path(temp_dir):
    """Create a copy of the PBIP project for testing."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "pbip_project"
    test_project_dir = temp_dir / "TestProject"
    test_project_dir.mkdir()
    
    # Copy .pbip file
    shutil.copy2(fixtures_dir / "TestCalcGroups.pbip", test_project_dir / "TestCalcGroups.pbip")
    
    # Copy semantic model directory
    shutil.copytree(
        fixtures_dir / "TestCalcGroups.SemanticModel", 
        test_project_dir / "TestCalcGroups.SemanticModel"
    )
    
    return test_project_dir / "TestCalcGroups.pbip"


@pytest.fixture
def project_parser():
    """Create a ProjectParser instance."""
    return ProjectParser()


@pytest.fixture
def tmdl_writer():
    """Create a TMDLWriter instance."""
    return TMDLWriter()


@pytest.fixture
def measure_operations(project_parser, tmdl_writer):
    """Create a MeasureOperations instance."""
    return MeasureOperations(project_parser, tmdl_writer)


@pytest.fixture
def column_operations(project_parser, tmdl_writer):
    """Create a ColumnOperations instance."""
    return ColumnOperations(project_parser, tmdl_writer)


@pytest.fixture
def table_operations(project_parser, tmdl_writer):
    """Create a TableOperations instance."""
    return TableOperations(project_parser, tmdl_writer)


@pytest.fixture
def relationship_operations(project_parser, tmdl_writer):
    """Create a RelationshipOperations instance."""
    return RelationshipOperations(project_parser, tmdl_writer)


@pytest.fixture
def sample_measure_args():
    """Sample arguments for measure operations."""
    return {
        "table_name": "Fact",
        "measure_name": "Test Measure",
        "expression": "SUM(Fact[Revenue])",
        "description": "A test measure",
        "format_string": "#,##0.00"
    }


@pytest.fixture
def sample_column_args():
    """Sample arguments for column operations."""
    return {
        "table_name": "Fact",
        "column_name": "Test Column",
        "data_type": "string",
        "expression": "LEFT(Fact[Customer], 10)",
        "format_string": "",
        "summarize_by": "none",
        "is_hidden": False
    }


@pytest.fixture(params=["standalone", "pbip"])
def test_project_path(request, standalone_semantic_model_path, pbip_project_path):
    """Parameterized fixture that provides both standalone and PBIP project paths."""
    if request.param == "standalone":
        return str(standalone_semantic_model_path)
    else:
        return str(pbip_project_path)


@pytest.fixture
def expected_tables():
    """Expected tables in the test project."""
    return [
        "DateTableTemplate_d590ddbc-c002-4bfd-b5d1-24a4366dfe16",
        "Fact",
        "LocalDateTable_26818a28-2e45-4734-83ad-c32aa92d15d9",
        "MetricName",
        "Month"
    ]


@pytest.fixture
def expected_fact_measures():
    """Expected measures in the Fact table."""
    return [
        "PlaceholderMeasure",
        "'Total Revenue'",
        "'Transaction Count'"
    ]


@pytest.fixture
def expected_fact_columns():
    """Expected columns in the Fact table."""
    return [
        "Customer",
        "Product", 
        "Revenue",
        "Gross Profit",
        "Date",
        "IdealRevenueCalcColumn"
    ]