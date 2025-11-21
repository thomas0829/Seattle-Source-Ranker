"""
Tests for utils/classify_languages.py
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.classify_languages import classify_by_name


class TestLanguageClassification:
    """Test language classification logic"""
    
    def test_python_keywords(self):
        """Test Python keyword detection"""
        assert classify_by_name('my-python-project') == 'Python'
        assert classify_by_name('django-app') == 'Python'
        assert classify_by_name('flask-server') == 'Python'
        assert classify_by_name('pytorch-model') == 'Python'
    
    def test_cpp_keywords(self):
        """Test C++ keyword detection"""
        assert classify_by_name('my-cpp-library') == 'C++'
        assert classify_by_name('opencv-project') == 'C++'
    
    def test_known_projects(self):
        """Test known project mappings"""
        assert classify_by_name('vscode') == 'TypeScript'
        assert classify_by_name('vscode-extension') == 'TypeScript'
        assert classify_by_name('powertoys') == 'C#'
        assert classify_by_name('terminal') == 'C++'
    
    def test_case_insensitivity(self):
        """Test that classification is case-insensitive"""
        assert classify_by_name('PYTHON-APP') == 'Python'
        assert classify_by_name('Python-App') == 'Python'
        assert classify_by_name('python-app') == 'Python'
    
    def test_unknown_project(self):
        """Test handling of unknown projects"""
        result = classify_by_name('some-random-project-xyz')
        assert result == 'Other'
    
    def test_empty_name(self):
        """Test handling of empty name"""
        result = classify_by_name('')
        assert result == 'Other'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
