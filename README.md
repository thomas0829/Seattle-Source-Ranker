# Seattle Source Ranker

[![Beta Version](https://img.shields.io/badge/version-Beta--v4.2-orange)](https://github.com/thomas0829/Seattle-Source-Ranker/releases/tag/Beta-v4.2)
[![Last Updated](https://img.shields.io/badge/auto--update-daily-brightgreen.svg)](https://github.com/thomas0829/Seattle-Source-Ranker/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Discover and rank open source projects from Seattle's tech community**

A comprehensive tool that collects, analyzes, and ranks open source projects from Seattle-based GitHub users. Features intelligent multi-factor scoring, distributed collection, and automated daily updates.

**Live Website**: [https://thomas0829.github.io/Seattle-Source-Ranker/](https://thomas0829.github.io/Seattle-Source-Ranker/)

---

## Latest Statistics

- **432,498 projects** tracked across Seattle's developer community
- **2,828,357 total stars** accumulated by Seattle projects
- **28,283 users** collected in latest run
- **1,074 Python projects** published on PyPI (1.99% of Python projects)
- **28 Python projects** in global Top 15,000 PyPI packages (0.07% of Python projects)
- Last updated: 2025-12-07 11:52:52 PST

---

## Target Audience & User Stories

### For Students
- **Portfolio Discovery**: "As a CS student, I want to discover high-quality Seattle projects to learn from real-world code"
- **Contribution Opportunities**: "I want to find active local projects where I can make meaningful contributions"
- **Technology Trends**: "I want to see what technologies Seattle developers are using to guide my learning path"
- **Networking**: "I want to identify influential developers in Seattle to follow and learn from"

### For Recruiters
- **Talent Discovery**: "As a recruiter, I want to find active Seattle developers based on their project quality and activity"
- **Skill Assessment**: "I want to see a developer's technical stack and project involvement at a glance"
- **Local Tech Landscape**: "I want to understand what technologies are trending in Seattle's developer community"
- **Company Research**: "I want to identify which companies have the most active open source presence in Seattle"

---

## Team & Contributions

| Team Member | Role | Contributions |
|------------|------|---------------|
| **thomas0829** | Project Lead & Full-Stack Developer | • System architecture & distributed processing<br>• Frontend/Backend implementation<br>• GitHub API integration & optimization<br>• PyPI integration & Python rankings<br>• Automated deployment & CI/CD |
| **Wenshu0206** | UI/UX Designer | • Mobile version design<br>• Homepage first version design |
| **Muwen320** | Scoring Algorithm Specialist | • SSR scoring algorithm design<br>• Algorithm documentation |
| **Chase-Zou** | Data Validation & Reliability Engineer | • Validation methods design<br>• Data quality assurance<br>• Verification mechanisms<br>• Integrity testing |

---

## Key Features

### Core Functionality
- **Distributed Processing** - 8 Celery workers with 16 concurrent tasks for efficient data collection
- **Smart API Usage** - GraphQL for user search (5000 req/hr), REST for repository data (5000 req/hr)
- **Multi-factor Scoring** - Comprehensive SSR algorithm balancing popularity, quality, and maintenance
- **Language Classification** - 11 major programming languages with separate rankings
- **Daily Auto-Updates** - Automated collection and deployment at midnight Seattle time

### Website Features
- **Dual Rankings Pages**:
  - **Overall Rankings** - Top 10,000 projects across all languages
  - **Python Rankings** - Dedicated page with PyPI integration and bonus scoring
- **Interactive UI** - React-based with real-time search, suggestions, and smooth pagination
- **Tiered PyPI Bonuses** - Python projects receive 5% bonus (any PyPI) + 10% bonus (Top 15k global)
- **Smart Search** - Debounced search with owner and topic suggestions
- **Glass Morphism Design** - Modern, professional aesthetic with smooth animations
- **Comprehensive Documentation** - Dedicated pages for scoring methodology and data validation

### Technical Excellence
- **Dual Data Sources** - Integrates GitHub API (user search via GraphQL, repository data via REST) and PyPI API (package verification)
- **Rate Limit Optimization** - 6 GitHub tokens with intelligent rotation
- **PyPI Detection** - Offline matching with 707k+ packages, 100% precision, tiered scoring for Top 15k
- **Comprehensive Testing** - 225 tests covering all core functionality
  - Test Coverage: **56%** of library code (100% for scoring module, 97% for PyPI detection, 94% for token management)
  - Core modules at 94-100% coverage ensuring reliability
  - Python: pylint code quality checks (8.72/10)
  - Frontend: JavaScript/JSX syntax validation, CSS structure checks
  - Shell: Bash script syntax validation, GitHub Actions YAML validation
  - Run tests: `pytest test/`
  - Generate coverage report: `pytest --cov=src/seattle_source_ranker --cov-report=html`
- **Organization Support** - Handles allenai, awslabs, FredHutch, and other Seattle organizations

---

## Quick Start

### View Live Rankings
Visit **[https://thomas0829.github.io/Seattle-Source-Ranker/](https://thomas0829.github.io/Seattle-Source-Ranker/)** to explore Seattle's open source projects.

### Installation

```bash
# Clone and install
git clone https://github.com/thomas0829/Seattle-Source-Ranker.git
cd Seattle-Source-Ranker
pip install -e .
```

### Simple Usage Examples

The package can be used as a library for analyzing GitHub projects:

#### Example 1: Calculate Project Score
```python
from seattle_source_ranker.scoring import calculate_github_score

project = {
    'stars': 1000,
    'forks': 150,
    'watchers': 200,
    'open_issues': 25,
    'created_at': '2020-01-01T00:00:00Z',
    'pushed_at': '2024-11-15T10:30:00Z'
}

score = calculate_github_score(project)
print(f"SSR Score: {score:.2f}")  # Output: SSR Score: 6842.35
```

#### Example 2: Check PyPI Publication
```python
from seattle_source_ranker.pypi import PyPIChecker

checker = PyPIChecker()

project = {
    'name': 'requests',
    'language': 'Python',
    'topics': ['http', 'python'],
    'description': 'Python HTTP library'
}

is_on_pypi = checker.check_project(project)
print(f"On PyPI: {is_on_pypi}")  # Output: On PyPI: True
```

#### Example 3: Manage GitHub Tokens
```python
from seattle_source_ranker.tokens import TokenManager

# Load tokens from .env.tokens or environment
tm = TokenManager()

# Get best available token
token = tm.get_token()

# Check rate limit
limit_info = tm.check_rate_limit()
print(f"Remaining: {limit_info['remaining']}")
```

See the **[examples/](examples/)** directory for more detailed usage examples.

### Full Data Collection Pipeline

For running the complete data collection system:

**Prerequisites:**
- Python 3.11+
- Redis server
- GitHub Personal Access Tokens (6 recommended)

**Installation:**
```bash
# Install with conda (includes all dependencies)
conda env create -f environment.yml
conda activate ssr

# Start Redis
sudo systemctl start redis-server
redis-cli ping  # Should return PONG

# Configure tokens in .env.tokens file
GITHUB_TOKEN_1=ghp_your_token_here
GITHUB_TOKEN_2=ghp_your_token_here
# ... up to GITHUB_TOKEN_6
```

**Usage Pipeline:**

#### 1. Data Collection (60-90 minutes)
```bash
python main.py --max-users 30000 --workers 8
```

#### 2. Secondary Update - Validate & Update Watchers (30-40 minutes)
```bash
# Start Redis (if not running)
redis-server --daemonize yes

# Start Celery workers
bash scripts/start_workers.sh

# Run secondary update
python scripts/secondary_update.py

# Stop workers when done
bash scripts/stop_workers.sh
```

#### 3. Generate PyPI List (< 1 minute)
```bash
python scripts/generate_pypi_projects.py
```

#### 4. Generate Frontend Data (30 seconds)
```bash
python scripts/generate_frontend_data.py
```

#### 5. Update README (< 1 second)
```bash
python scripts/update_readme.py
```

#### 6. Test Frontend (optional)
```bash
cd frontend && npm start  # http://localhost:3000
```

**Note:** Generated files (`data/seattle_projects_*.json`, `frontend/public/pages/`) stay local and are not committed to Git.

---

## Enhanced SSR Scoring Algorithm

Projects are ranked using a comprehensive multi-factor scoring system that balances popularity with quality and maintenance signals.

### Base Popularity Metrics (70%)
```
Stars    × 40%  - Primary popularity indicator
Forks    × 20%  - Engagement and derivative work
Watchers × 10%  - Ongoing interest and monitoring
```

### Quality Factors (30%)
```
Age      × 10%  - Project maturity (peak at 3-5 years)
Activity × 10%  - Recent maintenance (last push time)
Health   × 10%  - Issue management (issues relative to popularity)
```

### Scoring Formula
```
Score = (
    log₁₀(stars + 1) / log₁₀(100000) × 0.40 +
    log₁₀(forks + 1) / log₁₀(10000) × 0.20 +
    log₁₀(watchers + 1) / log₁₀(10000) × 0.10 +
    age_factor() × 0.10 +
    activity_factor() × 0.10 +
    health_factor() × 0.10
) × 1000000
```

### Python Projects: Tiered PyPI Bonuses

Python projects published on PyPI receive tiered scoring enhancements:

```
Base Score Range: 0-1,000,000 points

Tier 1 - Any PyPI Package:           Base Score × 1.05
Tier 2 - Top 15k Global PyPI:        Base Score × 1.05 × 1.10 = × 1.155

Examples:
  Not on PyPI:       756,000 points → 756,000 final
  Regular PyPI:      756,000 points → 793,800 final (+5%)
  Top 15k PyPI:      756,000 points → 873,180 final (+15.5%)
```

**Tier 1 - Any PyPI (5% bonus):**
- Applies to ~1,071 packages (2.74% of Python projects)
- **Distribution Commitment** - Package is ready for `pip install`
- **Ecosystem Integration** - Can be used as a dependency in other projects

**Tier 2 - Top 15k Global (additional 10% bonus):**
- Applies to ~28 packages (0.07% of Python projects)
- **Global Impact** - Millions of downloads worldwide
- **Production Scale** - Among most-used Python packages
- **Combined bonus**: ×1.155 total (+15.5%)

The tiered system rewards both PyPI publication and global ecosystem impact while maintaining fairness to development-focused repositories.

### Why This Approach?

- **Logarithmic Scaling** - Better distribution across projects of different sizes
- **Age Maturity** - Rewards established projects (2-8 years), penalizes too new/old
- **Recent Activity** - Prefers actively maintained projects
- **Health Metrics** - Considers issue management quality relative to popularity
- **Tiered PyPI Bonuses** - Recognizes both production-ready and globally-impactful Python packages
- **Backend Calculation** - All scoring done in backend, frontend displays final scores

Projects are ranked both **overall** and **by programming language** (11 categories).


See [ARCHITECTURE.md](doc/ARCHITECTURE.md) for detailed factor calculations.

---

## Troubleshooting

Having issues? Check the **[Troubleshooting Guide](doc/TROUBLESHOOTING.md)** for:
- Common errors and solutions (Redis, rate limits, collection failures)
- Frontend build issues
- Frequently Asked Questions (watchers, tokens, file management)

---

## Documentation

### Design Specifications
- **[Functional Specification](doc/functional_specification.md)** - User requirements, data sources, and use cases
- **[Component Specification](doc/component_specification.md)** - Software components, interactions, and implementation plan

### Technical Documentation
- **[ARCHITECTURE.md](doc/ARCHITECTURE.md)** - Complete system architecture, data flow, and component design
- **[VERSION_HISTORY.md](doc/VERSION_HISTORY.md)** - Project changelog and version history
- **[MULTI_TOKEN_GUIDE.md](doc/MULTI_TOKEN_GUIDE.md)** - GitHub token setup and rotation guide
- **[USER_STORIES.md](doc/USER_STORIES.md)** - Use cases and target audiences
- **[TROUBLESHOOTING.md](doc/TROUBLESHOOTING.md)** - Common issues and solutions

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **GitHub API** for providing comprehensive data access
- **Seattle's developer community** for creating amazing open source projects
- **Celery & Redis** for enabling distributed processing
- **React** for powering the interactive web interface

---

<div align="center">

**Seattle Source Ranker Beta v4.0** - Current version with performance optimization.

*Statistics automatically updated by GitHub Actions.*

Made with <3 for Seattle's tech community

</div>
