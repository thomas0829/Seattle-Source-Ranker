# Seattle Source Ranker

[![Version](https://img.shields.io/badge/version-v1.0-blue)](https://github.com/thomas0829/Seattle-Source-Ranker/releases/tag/v1.0)
[![Last Updated](https://img.shields.io/badge/auto--update-daily-brightgreen.svg)](https://github.com/thomas0829/Seattle-Source-Ranker/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Discover and rank open source projects from Seattle's tech community**

![Seattle Source Ranker](frontend/public/og-image.png)

A comprehensive system that collects, validates, and ranks open source projects from Seattle-based GitHub users. Features three-stage API collection strategy, intelligent multi-factor scoring, secondary validation workflow, distributed processing with Celery/Redis, PyPI integration, and automated daily updates via GitHub Actions.

**Live Website**: [https://thomas0829.github.io/Seattle-Source-Ranker/](https://thomas0829.github.io/Seattle-Source-Ranker/)

---

## Latest Statistics

- **432,909 projects** tracked across Seattle's developer community
- **2,830,662 total stars** accumulated by Seattle projects
- **28,308 users** collected in latest run
- **1,074 Python projects** published on PyPI (1.99% of Python projects)
- **28 Python projects** in global Top 15,000 PyPI packages (0.07% of Python projects)
- Last updated: 2025-12-11 01:45:49 PST

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
| **Wenshu0206** | Mobile UI/UX Designer | • Mobile responsive design<br>• Mobile interface optimization |
| **Muwen320** | Scoring Algorithm Specialist | • SSR scoring algorithm design<br>• Algorithm documentation |
| **Chase-Zou** | Data Validation & Reliability Engineer | • Validation methods design<br>• Data quality assurance<br>• Verification mechanisms<br>• Integrity testing |

---

## Key Features

### Core Functionality
- **Three-Stage API Strategy**:
  - **Stage 1 (GraphQL)**: Fast user discovery with flexible query syntax, 5000 req/hr per token
  - **Stage 2 (REST)**: Stable repo collection but watchers field returns incorrect data (stars instead)
  - **Stage 3 (GraphQL+HEAD)**: Fix watchers with real subscribers_count, validate repo accessibility
- **Secondary Validation** - Removes ~2% invalid repos (deleted/private/inaccessible), fixes incorrect watchers count
- **Distributed Processing** - 8 Celery workers × 2 concurrency = 16 parallel tasks for efficient collection
- **Token Rotation** - Multi-token support with intelligent rotation (6 tokens → ~60-90 min collection)
- **Multi-factor Scoring** - Comprehensive SSR algorithm balancing popularity, quality, and maintenance
- **Language Classification** - 10 major programming languages with separate rankings
- **Daily Auto-Updates** - Automated collection and deployment at midnight Seattle time via GitHub Actions

### Website Features
- **Dual Rankings Pages**:
  - **Overall Rankings** - Top 10,000 projects across all languages
  - **Python Rankings** - Dedicated page with PyPI integration and tiered bonus scoring
- **Interactive UI** - React 18+ based with real-time search, suggestions, and smooth pagination
- **Tiered PyPI Bonuses** - Python projects receive 5% bonus (any PyPI) + 10% bonus (Top 15K global)
- **Smart Search** - Debounced search with owner and topic suggestions, adaptive character matching
- **Glass Morphism Design** - Modern, professional aesthetic with smooth animations
- **Comprehensive Documentation** - Dedicated pages for scoring methodology and data validation

### Technical Excellence
- **Three Data Sources Integration** - GitHub API (~430K projects) + PyPI Official Packages (~700K) + Top 15K PyPI Rankings
- **Three-Stage API Collection** - GraphQL for fast user discovery → REST for stable repo data → GraphQL+HEAD for validation
- **Rate Limit Optimization** - Multi-token rotation (6 tokens recommended), GraphQL 5000 req/hr per token
- **PyPI Detection** - Offline matching with ~700K packages, 100% precision, tiered scoring for Top 15K
- **One-Command Pipeline** - `./run_local.sh` runs complete 11-step workflow automatically
- **Comprehensive Testing** - 225 tests with 56% overall coverage (100% scoring, 97% PyPI, 94% tokens)
- **Smart Search with 6 Data Tiers** - Adaptive character matching based on language popularity (1-5 chars)
- **Organization Support** - Handles allenai, awslabs, FredHutch, and other Seattle organizations

---

## Quick Start

### Installation

```bash
# Clone and install
git clone https://github.com/thomas0829/Seattle-Source-Ranker.git
cd Seattle-Source-Ranker
pip install -e .
```

### Simple Usage Examples

The package can be used as a library for analyzing GitHub projects. See the **[examples/](examples/)** directory for complete working examples.

#### Example 1: Token Management
```bash
python examples/example_1_token_management.py
```
Demonstrates how to:
- Load GitHub tokens from `.env.tokens`
- Get the best available token
- View all configured tokens

**Sample Output:**
```
✓ Loaded 6 GitHub tokens
✓ Current token: ghp_AxzS1Y...
✓ Total available tokens: 6
```

#### Example 2: PyPI Package Detection
```bash
python examples/example_2_pypi_checker.py
```
Demonstrates how to:
- Check if GitHub projects are published on PyPI
- Use individual and batch checking methods
- Interpret confidence scores and match reasons

**Sample Output:**
```
requests                       ✓ ON PyPI
                                 Confidence: 0.95 (direct_match_verified)
flask                          ✓ ON PyPI
                                 Confidence: 0.95 (direct_match_verified)
```

#### Example 3: Project Scoring
```bash
python examples/example_3_scoring.py
```
Demonstrates how to:
- Calculate SSR scores for GitHub projects
- Analyze age, activity, and health factors
- Rank projects by their scores

**Sample Output:**
```
High Quality Project:
  SSR Score: 796,364.00
  Stars: 5,000
  Age Factor: 0.93
  Activity Factor: 1.00
```

---

## Full Data Collection Pipeline

### Option 1: One-Command Execution (Recommended)

Run the complete pipeline with a single command:

```bash
./run_local.sh
```

**What it does:**
1. Auto-installs Conda environment if missing
2. Validates GitHub tokens in `.env.tokens` (configurable, 6 recommended)
3. Starts Redis server daemon
4. Runs primary collection (~60-90 min, ~430K projects)
5. Starts 8 Celery workers (16 parallel tasks)
6. Runs secondary validation (~45 min, fixes ~2% repos)
7. Stops workers automatically
8. Updates PyPI official package index
9. Generates PyPI project list
10. Checks Top 15K PyPI rankings
11. Generates frontend data and starts dev server

**Prerequisites:**
- Python 3.11+ (auto-installed via Conda)
- Redis server installed
- `.env.tokens` file with GitHub tokens (6 recommended for optimal performance)

### Option 2: Manual Step-by-Step

**Prerequisites:**
- Python 3.11+
- Redis server
- GitHub Personal Access Tokens (6 recommended for ~60-90 min collection)

**Installation:**
```bash
# Option A: Install with conda (recommended, includes all dependencies)
conda env create -f environment.yml
conda activate ssr

# Option B: Install with pip
pip install -e .

# Start Redis daemon
redis-server --daemonize yes
redis-cli ping  # Should return PONG

# Configure tokens in .env.tokens file (example with 6 tokens)
GITHUB_TOKEN_1=ghp_your_token_here
GITHUB_TOKEN_2=ghp_your_token_here
# ... add more tokens as needed (GITHUB_TOKEN_3, GITHUB_TOKEN_4, etc.)
```

**Collection Steps:**

#### 1. Primary Collection - Three-Stage API (~60-90 minutes)
```bash
python main.py --max-users 30000 --workers 8
```
- Stage 1: GraphQL user search (fast but unstable for bulk details)
- Stage 2: REST API repo collection (stable but watchers field wrong)
- Stage 3: GraphQL+HEAD validation (fix watchers, validate accessibility)

#### 2. Secondary Validation - Fix & Validate (~45 minutes)
```bash
# Start Celery workers (8 workers × 2 concurrency = 16 tasks)
bash scripts/start_workers.sh

# Run secondary validation
python scripts/secondary_update.py

# Stop workers when done
bash scripts/stop_workers.sh
```
- Removes ~2% invalid repos (deleted/private/HTTP 451)
- Fixes watchers count (REST returns stars, GraphQL returns real subscribers_count)

#### 3. Update PyPI Official Index (< 1 minute)
```bash
python scripts/update_pypi_official_index.py
```

#### 4. Generate PyPI Project List (< 1 minute)
```bash
python scripts/generate_pypi_projects.py
```

#### 5. Check Top 15K PyPI Rankings (< 1 minute)
```bash
python scripts/update_top_pypi_packages.py
```

#### 6. Generate Frontend Data (< 1 minute)
```bash
python scripts/generate_frontend_data.py
```

#### 7. Update README Statistics (< 1 second)
```bash
python scripts/update_readme.py
```

#### 8. Test Frontend (optional)
```bash
cd frontend && npm start  # http://localhost:3000
```

**Note:** Generated files (`data/seattle_projects.json`, `frontend/public/data/`) stay local and are not committed to Git.

---

## Testing

Run comprehensive test suite covering all core functionality:

```bash
# Run all tests
pytest test/

# Run with coverage report
pytest --cov=src/seattle_source_ranker --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Test Coverage:**
- **Overall**: 56% of library code
- **Core Modules**: 94-100% coverage
  - Scoring module: 100%
  - PyPI detection: 97%
  - Token management: 94%
- **Code Quality**: pylint 8.08/10
- **Test Types**: Unit tests, integration tests, syntax validation
- **Total Tests**: 225 tests across 12 test files

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
Tier 2 - Top 15K Global PyPI:        Base Score × 1.05 × 1.10 = × 1.155

Examples:
  Not on PyPI:       756,000 points → 756,000 final
  Regular PyPI:      756,000 points → 793,800 final (+5%)
  Top 15K PyPI:      756,000 points → 873,180 final (+15.5%)
```

**Tier 1 - Any PyPI (5% bonus):**
- Applies to ~1K packages (~2.7% of Python projects)
- **Distribution Commitment** - Package is ready for `pip install`
- **Ecosystem Integration** - Can be used as a dependency in other projects

**Tier 2 - Top 15K Global (additional 10% bonus):**
- Applies to ~30 packages (~0.07% of Python projects)
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

Projects are ranked both **overall** and **by programming language** (10 major categories: JavaScript, Python, HTML, Java, TypeScript, C#, Ruby, CSS, C++, Jupyter Notebook).

See [component_specification.md](doc/component_specification.md) for detailed factor calculations and scoring implementation.

---

## Troubleshooting

Having issues? Check the **[Troubleshooting Guide](doc/TROUBLESHOOTING.md)** for:
- Common errors and solutions (Redis, rate limits, collection failures)
- Frontend build issues
- Frequently Asked Questions (watchers, tokens, file management)

---

## Documentation

### Project Specifications
- **[Functional Specification](doc/functional_specification.md)** - User requirements, data sources, use cases, and system overview
- **[Component Specification](doc/component_specification.md)** - 7 software components, interactions, workflows, and implementation details

### Technical Documentation
- **[Version History](doc/VERSION_HISTORY.md)** - Project changelog and version history
- **[Multi Token Guide](doc/MULTI_TOKEN_GUIDE.md)** - 6-token setup, rotation strategy, and performance optimization
- **[User Stories](doc/USER_STORIES.md)** - Detailed user personas and use cases
- **[Troubleshooting](doc/TROUBLESHOOTING.md)** - Common issues, solutions, and FAQs

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **GitHub API** (GraphQL v4 + REST v3) for comprehensive data access
- **PyPI API** for Python package ecosystem data
- **Top 15K PyPI packages ranking** from [hugovk/top-pypi-packages](https://hugovk.github.io/top-pypi-packages/)
- **Seattle's developer community** for creating amazing open source projects
- **Celery & Redis** for enabling distributed processing and task queuing
- **React** for powering the interactive web interface
- **GitHub Actions** for automated daily workflows and deployment

---

<div align="center">

**Seattle Source Ranker v1.0** - Production-ready ranking system with advanced search and PyPI integration

*Statistics automatically updated daily by GitHub Actions at midnight Seattle time.*

Made with ❤️ for Seattle's tech community

</div>
