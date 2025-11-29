# Seattle Source Ranker

[![Beta Version](https://img.shields.io/badge/version-Beta--v4.0-orange)](https://github.com/thomas0829/Seattle-Source-Ranker/releases/tag/Beta-v4.0)
[![Last Updated](https://img.shields.io/badge/auto--update-daily-brightgreen.svg)](https://github.com/thomas0829/Seattle-Source-Ranker/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🏔️ **Discover and rank open source projects from Seattle's tech community**

A comprehensive tool that collects, analyzes, and ranks open source projects from Seattle-based GitHub users. Features intelligent multi-factor scoring, distributed collection, and automated daily updates.

🌐 **Live Website**: [https://thomas0829.github.io/Seattle-Source-Ranker/](https://thomas0829.github.io/Seattle-Source-Ranker/)

---

## 📊 Latest Statistics

- **465,160 projects** tracked across Seattle's developer community
- **2,830,438 total stars** accumulated by Seattle projects
- **28,251 users** collected in latest run
- **9,998 Python projects** published on PyPI (18.08% of Python projects)
- Last updated: 2025-11-29 00:30:46 PST

---

## 🎯 Target Audience & User Stories

### For Students 📚
- **Portfolio Discovery**: "As a CS student, I want to discover high-quality Seattle projects to learn from real-world code"
- **Contribution Opportunities**: "I want to find active local projects where I can make meaningful contributions"
- **Technology Trends**: "I want to see what technologies Seattle developers are using to guide my learning path"
- **Networking**: "I want to identify influential developers in Seattle to follow and learn from"

### For Recruiters 💼
- **Talent Discovery**: "As a recruiter, I want to find active Seattle developers based on their project quality and activity"
- **Skill Assessment**: "I want to see a developer's technical stack and project involvement at a glance"
- **Local Tech Landscape**: "I want to understand what technologies are trending in Seattle's developer community"
- **Company Research**: "I want to identify which companies have the most active open source presence in Seattle"

---

## 👥 Team & Contributions

| Team Member | Role | Contributions |
|------------|------|---------------|
| **thomas0829** | Project Architecture & System Design Lead | • Frontend/Backend system architecture<br>• GraphQL/REST API integration<br>• Distributed collection system (Celery + Redis)<br>• Rate limit handling & token rotation<br>• Python rankings with PyPI integration<br>• Performance optimization<br>• GitHub Actions automation |
| **Wenshu0206** | Frontend Developer & UI/UX Designer | • React frontend development<br>• Component design & implementation<br>• User experience optimization<br>• Responsive layout design<br>• UI/UX testing & refinement |
| **Muwen320** | Scoring Algorithm & Interpretability Specialist | • SSR scoring algorithm design<br>• Multi-factor ranking system<br>• Language classification logic<br>• Algorithm documentation<br>• Transparent scoring methodology |
| **Chase-Zou** | Data Validation & Reliability Engineer | • Validation methods design<br>• Data quality assurance<br>• Verification mechanisms<br>• Integrity testing<br>• Error handling & recovery |

---

## 🌟 Key Features

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
- **PyPI Integration** - Python projects receive 10% score bonus for PyPI publication
- **Smart Search** - Debounced search with owner and topic suggestions
- **Glass Morphism Design** - Modern, professional aesthetic with smooth animations
- **Comprehensive Documentation** - Dedicated pages for scoring methodology and data validation

### Technical Excellence
- **Rate Limit Optimization** - 6 GitHub tokens with intelligent rotation
- **PyPI Detection** - Offline matching with 702k+ packages, 100% precision
- **Comprehensive Testing** - 91 tests covering all core functionality
- **Organization Support** - Handles allenai, awslabs, FredHutch, and other Seattle organizations

---

## 🚀 Quick Start

### View the Data
Simply visit our **[live website](https://thomas0829.github.io/Seattle-Source-Ranker/)** to explore Seattle's open source projects.

### Run Collection Locally

**Prerequisites:**
- Python 3.11+
- Redis server
- GitHub Personal Access Tokens

**Setup:**
```bash
# 1. Clone repository
git clone https://github.com/thomas0829/Seattle-Source-Ranker.git
cd Seattle-Source-Ranker

# 2. Install dependencies (choose one method)

## Option A: Using conda
conda env create -f environment.yml
conda activate ssr

## Option B: Using pip
# Recommended for local development:
pip install -e .    # editable install (recommended for development)
# Or install from source (non-editable):
pip install .

# 3. Start Redis (System Service)
# Most Linux distributions come with Redis pre-installed
sudo systemctl start redis-server
sudo systemctl enable redis-server  # Auto-start on boot

# Check Redis is running
systemctl status redis-server
redis-cli ping  # Should return PONG

# Optional: If you prefer Docker instead
# docker run -d --name ssr-redis -p 6379:6379 redis:7-alpine

# 4. Configure tokens (create .env.tokens file)
GITHUB_TOKEN_1=ghp_your_token_here
GITHUB_TOKEN_2=ghp_your_token_here
# ... up to GITHUB_TOKEN_6

# 5. Run collection
python main.py --max-users 30000 --workers 8
```

---

## 🤖 Automated Daily Updates

✨ **Runs automatically at midnight Seattle time (00:00 PST)**

The GitHub Actions workflow handles everything:
- 🔍 Discovers Seattle developers (76 location filters)
- 📦 Collects up to 30,000 user repositories in parallel
- 🐍 Detects Python packages on PyPI (702k+ packages indexed)
- 📊 Ranks projects using SSR algorithm
- 🌐 Builds and deploys website to GitHub Pages
- 📝 Updates statistics in README
- 💾 Commits user data and PyPI data to Git

**Key Features:**
- Zero false positives in PyPI detection (100% precision)
- Offline matching for high performance (<30s for 55k projects)
- Comprehensive test suite with 91 passing tests
- Organization support (allenai, awslabs, FredHutch, etc.)

**Want to run it yourself?**
1. Fork this repository
2. Add 6 GitHub Personal Access Tokens as Secrets (`GH_TOKEN_1` - `GH_TOKEN_6`)
3. Ensure tokens have `read:org` scope for organization data
4. Enable GitHub Pages (Settings → Pages → `gh-pages` branch)
5. Workflow runs daily or trigger manually from Actions tab

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed workflow documentation.

---

## 📁 Project Structure

```
.
├── .github/
│   └── workflows/
│       └── collect-and-deploy.yml    # Daily automation
├── data/                             # Collection output
│   ├── seattle_projects_*.json       # Raw project data (~260MB, local only)
│   ├── seattle_users_*.json          # User metadata (in Git)
│   ├── seattle_pypi_projects.json    # PyPI packages (in Git)
│   └── pypi_official_packages.json   # PyPI index cache (in Git)
├── distributed/                      # Distributed collection system
│   ├── distributed_collector.py      # Main coordinator
│   ├── workers/
│   │   └── collection_worker.py      # Celery worker tasks
│   └── __init__.py
├── docs/                             # Extended documentation
│   ├── ARCHITECTURE.md               # System architecture details
│   ├── VERSION_HISTORY.md            # Complete changelog
│   ├── MULTI_TOKEN_GUIDE.md          # Token setup guide
│   └── USER_STORIES.md               # Use cases
├── frontend/                         # React web application
│   ├── src/
│   │   ├── App.js                    # Main component
│   │   ├── App.css                   # Glass morphism styling
│   │   ├── HomePage.js               # Landing page
│   │   ├── OverallRankingsPage.js    # Overall rankings page
│   │   ├── PythonRankingsPage.js     # Python rankings with PyPI
│   │   ├── ScoringPage.js            # Scoring methodology
│   │   ├── ValidationPage.js         # Data validation info
│   │   └── index.js
│   ├── public/
│   │   ├── pages/                    # Paginated JSON files
│   │   │   ├── python/               # Python project pages
│   │   │   ├── javascript/           # JavaScript project pages
│   │   │   └── ...                   # Other languages
│   │   ├── owner_index/              # Owner search index
│   │   ├── data/
│   │   │   └── seattle_pypi_projects.json  # PyPI data
│   │   └── metadata.json             # Stats & last updated
│   ├── build/                        # Production build
│   ├── package.json
│   ├── package-lock.json
│   └── .npmrc                        # npm configuration
├── scripts/                          # Automation scripts
│   ├── generate_frontend_data.py     # Generate paginated data
│   ├── generate_pypi_projects.py     # Generate PyPI project list
│   ├── update_readme.py              # Auto-update README stats
│   ├── start_workers.sh              # Start Celery workers
│   ├── stop_workers.sh               # Stop workers
│   ├── start_collection.sh           # Start collection process
│   └── test_workflow.sh              # Local testing
├── test/                             # Test suite (91 tests)
│   ├── test_token_manager.py         # Token rotation tests (21 tests)
│   ├── test_scoring_algorithms.py    # SSR scoring tests (40 tests)
│   ├── test_distributed_collector.py # Distributed system tests (12 tests)
│   ├── test_pypi_checker_full.py     # PyPI detection tests (14 tests)
│   ├── test_graphql_queries.py       # GraphQL query tests (4 tests)
│   ├── test_update_readme.py         # README update tests (5 tests)
│   ├── test_classify_languages.py    # Language classification tests (6 tests)
│   ├── test_pypi_50_projects.py      # Integration test (1 test)
│   ├── run_tests.sh                  # Test runner
│   └── pytest.ini                    # Pytest configuration
├── utils/                            # Utility modules
│   ├── token_manager.py              # Multi-token rotation
│   ├── classify_languages.py         # Language classification
│   ├── celery_config.py              # Celery configuration
│   ├── pypi_checker.py               # PyPI package detection
│   └── pypi_client.py                # PyPI package info
├── .gitattributes                    # Git LFS configuration
├── .gitignore
├── environment.yml                   # Conda environment specification
├── pyproject.toml                    # Python project metadata
├── pytest.ini                        # Pytest configuration
├── LICENSE
└── README.md
```

---

## 🧮 Enhanced SSR Scoring Algorithm

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
) × 10000
```

### Python Projects: PyPI Bonus (10%)

Python projects published on PyPI receive an additional scoring enhancement:

```
Python Final Score = Base SSR Score × 1.1  (if on PyPI)
                   = Base SSR Score × 1.0  (if not on PyPI)
```

**Why PyPI matters:**
- **Distribution Commitment** - Package is ready for `pip install`
- **Ecosystem Integration** - Can be used as a dependency in other projects
- **Maintenance Signal** - Publication indicates production readiness
- **Community Reach** - Discoverable beyond GitHub

The 10% bonus rewards projects that contribute to Python's package ecosystem while maintaining fairness to development-focused repositories.

### Why This Approach?

- **Logarithmic Scaling** - Better distribution across projects of different sizes
- **Age Maturity** - Rewards established projects (2-8 years), penalizes too new/old
- **Recent Activity** - Prefers actively maintained projects
- **Health Metrics** - Considers issue management quality relative to popularity
- **PyPI Integration** - Recognizes production-ready Python packages

Projects are ranked both **overall** and **by programming language** (11 categories).

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed factor calculations.

---

## 🔧 Troubleshooting

**Redis Connection Error:**
```bash
# Check if Redis system service is running
systemctl status redis-server
sudo systemctl start redis-server  # Start if stopped

# Test Redis connection
redis-cli ping  # Should return PONG
```

**Rate Limit Issues:**
- Check token validity in `.env.tokens`
- Verify token rotation is working (logs show which token is active)
- Add more tokens if needed (up to 6 supported)

**Collection Failures:**
- Review GitHub Actions logs
- Ensure all 6 tokens are added as Secrets
- Check `.collection_success` marker exists before cleanup

**Frontend Build Issues:**
```bash
cd frontend
npm install
npm run build
```

---

## 📖 Documentation

- **[Architecture Details](docs/ARCHITECTURE.md)** - System components, data pipeline, performance metrics
- **[Version History](docs/VERSION_HISTORY.md)** - Complete changelog from v1.0 to current
- **[Live Website](https://thomas0829.github.io/Seattle-Source-Ranker/)** - Interactive data exploration

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **GitHub API** for providing comprehensive data access
- **Seattle's developer community** for creating amazing open source projects
- **Celery & Redis** for enabling distributed processing
- **React** for powering the interactive web interface

---

<div align="center">

**Seattle Source Ranker Beta v4.0** - Current version with performance optimization.

*Statistics automatically updated by GitHub Actions.*

Made with ❤️ for Seattle's tech community

</div>
