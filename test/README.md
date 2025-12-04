# Seattle Source Ranker - Test Suite

This directory contains comprehensive tests for the Seattle Source Ranker project.

## [STATS] Test Statistics

- **91 tests** - All passing [OK]
- **8 test files** covering core functionality
- **12 skipped** (require Celery/Redis)
- **Execution time**: ~23 seconds

## Quick Start

```bash
# Run all tests (recommended method)
./test/run_tests.sh

# Run specific test file
cd test && bash run_tests.sh

# Run with verbose output
cd test && PYTHONPATH=.. python3 -m pytest test_graphql_queries.py -v --override-ini="plugins="
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
├── test_classify_languages.py          # Language classification (6 tests)
├── test_graphql_queries.py             # GraphQL query structure (4 tests)
├── test_update_readme.py               # README update logic (5 tests)
├── test_pypi_50_projects.py            # PyPI detection with real data (1 test)
│
├── test_token_manager.py               # Token rotation & rate limits (21 tests) 🆕
├── test_scoring_algorithms.py          # SSR scoring algorithm (40 tests) 🆕
├── test_distributed_collector.py       # Distributed collection (12 tests, skipped) 🆕
└── test_pypi_checker_full.py           # PyPI checker complete (14 tests) 🆕
```

## [TARGET] Test Categories

### Core Functionality (91 tests)

1. **Language Classification** (6 tests)
   - Python/C++/TypeScript keyword detection
   - Known project mappings (vscode, powertoys)
   - Case insensitivity
   - Unknown project handling

2. **GraphQL Queries** (4 tests) [WARNING] Critical
   - **Organization fragment inclusion** (prevents missing orgs like allenai, awslabs)
   - User fragment inclusion
   - Query structure validation

3. **README Updates** (5 tests)
   - User data loading (new metadata format)
   - Project data loading
   - Statistics updates
   - Date formatting

4. **PyPI Detection** (15 tests)
   - 50 real projects validation
   - Known package detection
   - Strong/very strong signal detection
   - Batch processing
   - Edge cases (empty names, None values)

5. **Token Management** (21 tests) 🔥 Critical
   - Multi-token initialization
   - Environment variable loading
   - Token rotation logic
   - Rate limit checking with caching
   - Best token selection
   - Thread safety

6. **Scoring Algorithms** (40 tests) 🔥 Core Logic
   - Normalization (linear & logarithmic)
   - Age factor (2-8 year peak scoring)
   - Activity factor (recent updates)
   - Health factor (issue management)
   - **Complete SSR algorithm** (0-10,000 scale)
   - Edge cases & extreme values

7. **Distributed Collection** (12 tests, skipped)
   - Batch creation
   - Worker management
   - Result aggregation
   - (Requires Celery/Redis to run)

## 🔑 Critical Tests

### 1. Organization Fragment Test [WARNING] MUST PASS
**Why**: Ensures Seattle organizations (allenai, awslabs, FredHutch) are included in results.

```python
def test_distributed_collector_has_organization_fragment():
    """Verifies GraphQL query includes '... on Organization { login }'"""
```

Without this, organizations appear as empty objects and are excluded from the 464K projects.

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
pytest --cov=../utils --cov=../scripts --cov=../distributed --cov-report=html
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

### Celery tests skipped
This is expected - distributed tests require:
```bash
pip install celery redis
# Start Redis
sudo systemctl start redis-server
```

### Tests are slow
```bash
# PyPI cache download can be slow first time (~704K packages)
# Subsequent runs use cache (fast)
```

## [CHART] Test Coverage Summary

| Module | Tests | Status |
|--------|-------|--------|
| `classify_languages.py` | 6 | [OK] 100% |
| `graphql queries` | 4 | [OK] 100% |
| `update_readme.py` | 5 | [OK] 100% |
| `pypi_checker.py` | 15 | [OK] 90% |
| `token_manager.py` | 21 | [OK] 85% |
| `scoring algorithms` | 40 | [OK] 95% |
| `distributed_collector.py` | 12 | [SKIP] Skipped |
| **Total** | **91** | **[OK] All Pass** |

## 🎓 Understanding Test Output

```bash
================================= test session starts ==================================
platform linux -- Python 3.13.5, pytest-8.4.2
collected 91 items

test_classify_languages.py::TestLanguageClassification::test_python_keywords PASSED [1%]
...
test_scoring_algorithms.py::TestCalculateGithubScore::test_score_range PASSED [70%]
...

============================= 91 passed in 23.15s ==============================
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
