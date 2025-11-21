# Seattle Source Ranker - Test Suite

This directory contains all tests for the Seattle Source Ranker project.

## Quick Start

```bash
# Run all tests (recommended method)
./test/run_tests.sh

# Run specific test file
cd test && PYTHONPATH=/home/thomas/Seattle-Source-Ranker python3 -m pytest test_graphql_queries.py -v --override-ini="plugins="
```

## Setup

Tests use pytest. No additional installation needed if pytest is already available.

```bash
pip install pytest  # If not installed
```

## Test Structure

```
test/
├── __init__.py                      # Test package initialization
├── README.md                        # This file
├── test_graphql_queries.py          # GraphQL query structure tests
├── test_update_readme.py            # README update script tests
└── test_classify_languages.py       # Language classification tests
```

## Test Categories

### Unit Tests
- `test_classify_languages.py` - Language classification logic
- `test_update_readme.py` - README update functionality

### Integration Tests  
- `test_graphql_queries.py` - GraphQL query structure validation

## Key Tests

### 1. Organization Fragment Test
**Critical Test**: Ensures organizations (like allenai, awslabs) are included in data collection.

```python
def test_distributed_collector_has_organization_fragment():
    """Verifies GraphQL query includes '... on Organization { login }'"""
```

**Why this matters**: Without the Organization fragment, organizations appear as empty objects and are excluded from results.

### 2. README Update Tests
Tests that README statistics are correctly updated from both:
- User data files (always available in Git)
- Project data files (generated during workflow runs)

### 3. Language Classification Tests
Validates that programming languages are correctly categorized for filtering.

## Continuous Integration

These tests can be integrated into GitHub Actions:

```yaml
- name: Run tests
  run: |
    pip install pytest pytest-cov
    pytest --cov --cov-report=xml
```

## Writing New Tests

1. Create a new file: `test/test_<module>.py`
2. Import pytest: `import pytest`
3. Create test classes: `class Test<Feature>:`
4. Write test functions: `def test_<behavior>():`
5. Use descriptive names and docstrings

Example:
```python
class TestNewFeature:
    """Test new feature functionality"""
    
    def test_basic_behavior(self):
        """Test that feature works correctly"""
        result = my_function()
        assert result == expected_value
```

## Current Test Coverage

- ✅ GraphQL query structure (Organization inclusion)
- ✅ README update logic (with/without project data)
- ✅ Language classification
- 🔲 Token management (TODO)
- 🔲 Data collection workflow (TODO)
- 🔲 Scoring algorithms (TODO)

## Troubleshooting

### ImportError: No module named 'xxx'
Make sure you're running from the project root:
```bash
cd /home/thomas/Seattle-Source-Ranker
pytest
```

### Tests can't find modules
Tests add parent directory to sys.path automatically. If issues persist, check PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:/home/thomas/Seattle-Source-Ranker"
```

### Fixture errors
Ensure pytest is installed correctly:
```bash
pip install --upgrade pytest
```
