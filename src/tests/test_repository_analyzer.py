# tests/test_repository_analyzer.py

import pytest
from src.agents.repository_analyzer import RepositoryAnalyzer

def test_clone_repository():
    """Test repository cloning"""
    analyzer = RepositoryAnalyzer("https://github.com/spring-projects/spring-petclinic")
    repo_path = analyzer.clone_repository()
    
    assert os.path.exists(repo_path)
    assert os.path.exists(os.path.join(repo_path, "pom.xml"))

def test_discover_files():
    """Test file discovery and categorization"""
    analyzer = RepositoryAnalyzer("https://github.com/spring-projects/spring-petclinic")
    analyzer.repo_path = "/path/to/cloned/repo"
    
    file_map = analyzer.discover_files()
    
    assert "controllers" in file_map
    assert "services" in file_map
    assert "repositories" in file_map
    assert len(file_map["controllers"]) > 0

def test_detect_build_system():
    """Test build system detection"""
    analyzer = RepositoryAnalyzer("...")
    analyzer.repo_path = "/path/with/pom.xml"
    
    assert analyzer.detect_build_system() == "maven"