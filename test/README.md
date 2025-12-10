# Seattle Source Ranker - Test Suite

This directory contains comprehensive tests for the Seattle Source Ranker project.

## [STATS] Test Statistics

- **225 tests** - All passing [OK]
- **12 test files** covering core functionality
- **0 skipped** (all tests executable)
- **Execution time**: ~52 seconds

## Quick Start

```bash
# Run all tests (recommended method)
cd test && bash run_tests.sh

# Run specific test file
cd test && bash run_tests.sh test_token_manager.py

# Run with verbose output
cd test && export PYTHONPATH=/home/thomas/Seattle-Source-Ranker && python3 -m pytest test_graphql_queries.py -v --override-ini="plugins="
```

## Setup

Tests use pytest. Install if needed:

```bash
pip install pytest pytest-mock
```

## 📁 Test Structure

```
test/
├── __init__.py                         # Test package initialization
├── README.md                           # This file
├── pytest.ini                          # Pytest configuration
├── run_tests.sh                        # Test runner script
│
├── test_code_style.py                  # Code quality & pylint checks
├── test_collection_worker.py           # Collection worker logic
├── test_distributed_collector.py       # Distributed collection system
├── test_frontend_syntax.py             # Frontend JavaScript/React validation
├── test_graphql_queries.py             # GraphQL query structure
├── test_integration_collection.py      # Celery/Redis integration (2 skipped)
├── test_pypi_checker_full.py           # PyPI package matching
├── test_pypi_client.py                 # PyPI API client
├── test_scoring_algorithms.py          # SSR scoring algorithms
├── test_shell_scripts.py               # Shell script validation
├── test_token_manager.py               # GitHub token management
└── test_update_readme.py               # README auto-update logic
```

## [TARGET] Test Categories

### Core Functionality (225 tests, all passing)

1. **Code Style & Quality**
   - Pylint score validation
   - Syntax error detection
   - Import structure verification
   - Documentation completeness

2. **Collection Worker**
   - Worker task execution
   - Batch processing logic
   - Error handling

3. **Distributed Collector**
   - Batch creation
   - User file discovery
   - Data aggregation

4. **Frontend Validation**
   - JavaScript/React syntax checking
   - Component structure validation
   - Build artifact verification

5. **GraphQL Queries** [WARNING] Critical
   - **Organization fragment inclusion** (prevents missing orgs like allenai, awslabs)
   - User fragment inclusion
   - Query structure validation

6. **Integration Tests**
   - Celery task execution
   - Redis connection
   - Worker status check

7. **PyPI Checker**
   - Package name matching
   - Verified/unverified detection
   - Signal strength calculation
   - Edge cases handling

8. **PyPI Client**
   - API interaction
   - Data parsing
   - Error handling

9. **Scoring Algorithms** 🔥 Core Logic
   - Normalization (linear & logarithmic)
   - Age factor (2-8 year peak scoring)
   - Activity factor (recent updates)
   - Health factor (issue management)
   - **Complete SSR algorithm** (0-10,000 scale)
   - Edge cases & extreme values

10. **Shell Scripts**
    - Bash syntax validation
    - Shebang presence
    - Execute permissions
    - GitHub Actions workflow validation

11. **Token Management** 🔥 Critical
    - Multi-token initialization
    - Environment variable loading
    - Token rotation logic
    - Rate limit checking with caching
    - Best token selection
    - Thread safety

12. **README Updates**
    - User data loading
    - Project data loading
    - Statistics updates
    - Date formatting

## 🔑 Critical Tests

### 1. Organization Fragment Test [WARNING] MUST PASS
**Why**: Ensures Seattle organizations (allenai, awslabs, FredHutch) are included in results.

```python
def test_known_seattle_organizations():
    """Verifies GraphQL query includes '... on Organization { login }'"""
```

Without this, organizations appear as empty objects and are excluded from projects.

### 2. SSR Scoring Algorithm Tests [TARGET]
**Why**: Validates that the ranking algorithm correctly scores projects.

- Projects aged 2-8 years get highest scores (peak maturity)
- Recently updated projects score higher (active maintenance)
- Low issue/star ratio indicates project health
- Final score: 0-10,000 (not 0-100!)

### 3. Token Manager Tests 🔐
**Why**: Prevents rate limit failures in production.

- Validates 6-token rotation system
- Tests rate limit caching (reduces API calls)
- Ensures thread-safe access

## [DIR] Data Dependencies

### [WARNING] Important: Test Data Paths

Tests use **project root `data/` directory**, not test-local data:

```python
# Correct [OK]
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
checker = PyPIChecker(cache_dir=str(DATA_DIR))

# Wrong [ERROR] - creates test/data/
checker = PyPIChecker()  # Uses CWD
```

**Required data files** (in `/home/thomas/Seattle-Source-Ranker/data/`):
- `pypi_official_packages.json` - 704K+ package names (cached from PyPI)
- `seattle_projects_*.json` - Project data (for test_pypi_50_projects.py)
- `seattle_users_*.json` - User data (optional)

## [START] Running Tests

### All Tests
```bash
cd test
bash run_tests.sh
```

### Specific Category
```bash
# Only scoring tests
pytest test_scoring_algorithms.py -v

# Only token tests
pytest test_token_manager.py -v

# Skip slow tests
pytest -m "not slow"
```

### With Coverage
```bash
pip install pytest-cov
pytest --cov=src/seattle_source_ranker --cov-report=html
# Open htmlcov/index.html
```

## ✍️ Writing New Tests

### Template
```python
#!/usr/bin/env python3
"""Tests for <module>"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from <module> import <function>

class TestFeature:
    """Test feature functionality"""
    
    def test_basic_behavior(self):
        """Test that feature works correctly"""
        result = my_function()
        assert result == expected_value
```

### Best Practices
- [OK] Use descriptive test names (`test_age_factor_peak_range` not `test_1`)
- [OK] Add docstrings explaining what's tested
- [OK] Group related tests in classes
- [OK] Use `@pytest.mark.skip` for tests requiring external services
- [OK] Mock external API calls to avoid rate limits
- [OK] Test edge cases (None, empty, negative values)

## 🔧 Troubleshooting

### ImportError: No module named 'xxx'
```bash
# Run from project root or use run_tests.sh
cd /home/thomas/Seattle-Source-Ranker/test
bash run_tests.sh
```

### Data files not found
```bash
# Ensure PyPI cache exists
ls -lh ../data/pypi_official_packages.json

# If missing, run PyPI download script
cd ..
python scripts/generate_pypi_projects.py
```

### Running integration tests
Integration tests require Celery workers to be running:
```bash
pip install celery redis
# Start Redis
sudo systemctl start redis-server
# Start Celery workers (required for full test coverage)
cd scripts && bash start_workers.sh
# Run tests
cd test && bash run_tests.sh
```

### Tests are slow
```bash
# PyPI cache download can be slow first time (~704K packages)
# Subsequent runs use cache (fast)
```

## [CHART] Test Coverage Summary

| Test File | Status |
|-----------|--------|
| `test_code_style.py` | [OK] Pass |
| `test_collection_worker.py` | [OK] Pass |
| `test_distributed_collector.py` | [OK] Pass |
| `test_frontend_syntax.py` | [OK] Pass |
| `test_graphql_queries.py` | [OK] Pass |
| `test_integration_collection.py` | [OK] Pass |
| `test_pypi_checker_full.py` | [OK] Pass |
| `test_pypi_client.py` | [OK] Pass |
| `test_scoring_algorithms.py` | [OK] Pass |
| `test_shell_scripts.py` | [OK] Pass |
| `test_token_manager.py` | [OK] Pass |
| `test_update_readme.py` | [OK] Pass |
| **Total** | **225 tests (all passing)** |

## 🎓 Understanding Test Output

```bash
================================= test session starts ==================================
platform linux -- Python 3.11.14, pytest-8.4.2
collected 225 items

test_code_style.py::TestCodeStyle::test_no_syntax_errors PASSED [1%]
...
test_token_manager.py::TestTokenManagerInit::test_init_with_tokens PASSED [90%]
...
test_update_readme.py::TestDateFormatting::test_iso_date_parsing PASSED [100%]

============================= 225 passed in 52.45s =============================
[OK] All tests passed!
```

### Status Indicators:
- [OK] `PASSED` - Test succeeded
- [ERROR] `FAILED` - Test failed (see error details)
- [SKIP] `SKIPPED` - Test skipped (requires Celery/Redis)
- [WARNING] Warning - Non-critical issue (e.g., deprecation)

## [RETRY] Continuous Integration

Add to `.github/workflows/test.yml`:

```yaml
- name: Run tests
  run: |
    cd test
    bash run_tests.sh
    
- name: Upload coverage
  if: matrix.python-version == '3.11'
  run: |
    pip install pytest-cov codecov
    pytest --cov --cov-report=xml
    codecov
```
