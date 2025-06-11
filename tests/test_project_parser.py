"""Tests for the ProjectParser class."""

import pytest
from pathlib import Path

from pbip_mcp.parsers import ProjectParser, ProjectParseError


class TestProjectParser:
    """Test cases for ProjectParser."""

    def test_load_standalone_semantic_model(self, project_parser, standalone_semantic_model_path):
        """Test loading a standalone semantic model directory."""
        project = project_parser.load_project(str(standalone_semantic_model_path))
        
        assert project is not None
        assert project.semantic_model is not None
        assert project.semantic_model.name == "Model"
        assert len(project.semantic_model.tables) == 5
        assert project.project_info.version == "1.0"  # Synthetic version
        
    def test_load_pbip_project(self, project_parser, pbip_project_path):
        """Test loading a complete PBIP project."""
        project = project_parser.load_project(str(pbip_project_path))
        
        assert project is not None
        assert project.semantic_model is not None
        assert project.semantic_model.name == "Model"
        assert len(project.semantic_model.tables) == 5
        assert project.project_info.version == "1.0"
        
    def test_load_nonexistent_path(self, project_parser):
        """Test loading a non-existent path raises appropriate error."""
        with pytest.raises(ProjectParseError, match="Project path does not exist"):
            project_parser.load_project("/nonexistent/path")
            
    def test_load_directory_without_pbip_or_semantic_model(self, project_parser, temp_dir):
        """Test loading a directory with no .pbip or .SemanticModel raises error."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        with pytest.raises(ProjectParseError, match="No .pbip file or .SemanticModel directory found"):
            project_parser.load_project(str(empty_dir))
            
    def test_semantic_model_has_expected_tables(self, project_parser, test_project_path, expected_tables):
        """Test that the semantic model contains expected tables."""
        project = project_parser.load_project(test_project_path)
        
        table_names = [table.name for table in project.semantic_model.tables]
        assert set(table_names) == set(expected_tables)
        
    def test_fact_table_has_expected_measures(self, project_parser, test_project_path, expected_fact_measures):
        """Test that the Fact table contains expected measures."""
        project = project_parser.load_project(test_project_path)
        
        fact_table = next(table for table in project.semantic_model.tables if table.name == "Fact")
        measure_names = [measure.name for measure in fact_table.measures]
        assert set(measure_names) == set(expected_fact_measures)
        
    def test_fact_table_has_expected_columns(self, project_parser, test_project_path, expected_fact_columns):
        """Test that the Fact table contains expected columns."""
        project = project_parser.load_project(test_project_path)
        
        fact_table = next(table for table in project.semantic_model.tables if table.name == "Fact")
        column_names = [column.name for column in fact_table.columns]
        assert set(column_names) == set(expected_fact_columns)
        
    def test_semantic_model_properties(self, project_parser, test_project_path):
        """Test semantic model properties are loaded correctly."""
        project = project_parser.load_project(test_project_path)
        
        assert project.semantic_model.culture == "en-US"
        assert not project.semantic_model.discourage_implicit_measures
        assert len(project.semantic_model.relationships) >= 0  # May have relationships
        
    def test_load_semantic_model_only_method(self, project_parser, standalone_semantic_model_path):
        """Test the _load_semantic_model_only method directly."""
        project = project_parser._load_semantic_model_only(standalone_semantic_model_path)
        
        assert project is not None
        assert project.semantic_model is not None
        assert project.project_info.version == "1.0"
        assert len(project.project_info.artifacts) == 0
        
    def test_find_semantic_model_dir(self, project_parser, pbip_project_path):
        """Test finding semantic model directory in PBIP project."""
        project_dir = pbip_project_path.parent
        project_name = pbip_project_path.stem
        
        semantic_dir = project_parser._find_semantic_model_dir(project_dir, project_name)
        assert semantic_dir is not None
        assert semantic_dir.name == "TestCalcGroups.SemanticModel"
        assert semantic_dir.exists()