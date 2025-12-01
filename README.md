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

- **465,222 projects** tracked across Seattle's developer community
- **2,830,750 total stars** accumulated by Seattle projects
- **28,251 users** collected in latest run
- **9,999 Python projects** published on PyPI (18.08% of Python projects)
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

## Quick Start

### View Live Rankings
Visit **[https://thomas0829.github.io/Seattle-Source-Ranker/](https://thomas0829.github.io/Seattle-Source-Ranker/)** to explore Seattle's open source projects.

### Local Development Setup

**Prerequisites:**
- Python 3.11+
- Redis server
- GitHub Personal Access Tokens (6 recommended)

**Installation:**
```bash
# 1. Clone repository
git clone https://github.com/thomas0829/Seattle-Source-Ranker.git
cd Seattle-Source-Ranker

# 2. Install dependencies
conda env create -f environment.yml
conda activate ssr
# Or: pip install -e .

# 3. Start Redis
sudo systemctl start redis-server
redis-cli ping  # Should return PONG

# 4. Configure tokens (.env.tokens file)
GITHUB_TOKEN_1=ghp_your_token_here
GITHUB_TOKEN_2=ghp_your_token_here
# ... up to GITHUB_TOKEN_6

# 5. Run collection
python main.py --max-users 30000 --workers 8
```

---

## File Management

### Local-Only Files
These files persist on your machine and are never committed to Git:

**Configuration:**
- `.env.tokens` - Your GitHub tokens (NEVER commit)
- `.collection_success` - Collection completion marker

**Generated Data:**
- `data/seattle_projects_*.json` - Full dataset (~260MB)
- `frontend/public/pages/` - Paginated JSON files (~9,150 files)
- `frontend/public/owner_index/` - Owner search index
- `frontend/public/metadata.json` - Statistics
- `frontend/build/` - React production build
- `logs/` - Collection logs

### Committed to Git
**Small Data Files:**
- `data/seattle_users_*.json` - User metadata (~20KB)
- `data/seattle_pypi_projects.json` - PyPI project list
- `data/pypi_official_packages.json` - Official PyPI packages

**Code & Config:**
- Source code, documentation, configuration files

**Note:** Generated frontend files are recreated during GitHub Actions deployment - no need to commit them locally.

---

## Complete Usage Workflow

### Manual Pipeline

#### 1. Data Collection (60-90 minutes)
```bash
python main.py --max-users 30000 --workers 8
```
→ Output: `data/seattle_projects_YYYYMMDD_HHMMSS.json` (~260MB)

#### 2. Update Watchers (30-40 minutes)
```bash
python scripts/update_watchers.py --workers 8
```
→ Fetches real subscriber counts via GraphQL  
→ Validates repository accessibility  
→ Removes deleted/blocked repos (~2%)

#### 3. Generate PyPI List (< 1 minute)
```bash
python scripts/generate_pypi_projects.py
```
→ Output: `data/seattle_pypi_projects.json`

#### 4. Generate Frontend Data (30 seconds)
```bash
python scripts/generate_frontend_data.py
```
→ Creates ~9,150 paginated JSON files

#### 5. Update README (< 1 second)
```bash
python scripts/update_readme.py
```
→ Updates statistics in README

#### 6. Build Frontend (optional, for local testing)
```bash
cd frontend
npm install      # First time only
npm start        # Development server at http://localhost:3000
```

#### 7. Commit Metadata (optional, if you want to save to Git)
```bash
git add data/seattle_users_*.json data/seattle_pypi_projects.json README.md
git commit -m "chore: Update data - $(date +'%Y-%m-%d')"
git push
```

**Total Time:** ~90-120 minutes (steps 1-5 required, 6-7 optional)

### Automated Daily Updates

GitHub Actions runs the complete pipeline automatically at midnight Seattle time:
1. Collection → 2. Watchers → 3. PyPI → 4. Frontend → 5. Build → 6. Deploy → 7. Commit

See `.github/workflows/collect-and-deploy.yml` for details.

---

## System Architecture

For detailed technical documentation, see:
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Complete system architecture, data flow, and component design
- **[VERSION_HISTORY.md](docs/VERSION_HISTORY.md)** - Project changelog and version history
- **[MULTI_TOKEN_GUIDE.md](docs/MULTI_TOKEN_GUIDE.md)** - GitHub token setup and rotation guide
- **[USER_STORIES.md](docs/USER_STORIES.md)** - Use cases and target audiences

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

## Troubleshooting

### Common Issues

**Redis Connection Error:**
```bash
# Check if Redis system service is running
systemctl status redis-server
sudo systemctl start redis-server  # Start if stopped

# Test Redis connection
redis-cli ping  # Should return PONG
```

**Rate Limit Issues:**
- **Check token validity**: Ensure all tokens in `.env.tokens` are valid
- **Verify token rotation**: Logs show which token is active
- **Add more tokens**: Supports up to 6 tokens (currently using 6)
- **Check rate limits**: Each token has 5,000 GraphQL + 5,000 REST requests/hour

**Collection Failures:**
- **Review logs**: Check `logs/YYYYMMDD/` for error messages
- **GitHub Actions**: Verify all 6 tokens are added as Secrets
- **Cleanup issues**: Ensure `.collection_success` marker exists before cleanup
- **Worker timeout**: Increase timeout in `celery_config.py` if needed

**Frontend Build Issues:**
```bash
cd frontend
rm -rf node_modules package-lock.json  # Clean install
npm install
npm run build
```

**Watchers Update Slow:**
```bash
# Use 8 workers for faster processing (8x speedup)
python scripts/update_watchers.py --workers 8

# Single-threaded (slow): ~5 hours
# 8 workers (recommended): ~30-40 minutes
```

### Frequently Asked Questions

**Q: Why are watchers much lower than stars?**  
A: `watchers` = GitHub subscribers (notifications), `stars` = bookmarks. Typically 0.5%-4% ratio is normal. Projects with 10,000 stars often have only 50-400 watchers.

**Q: Why were some repositories removed?**  
A: ~2% of repos become inaccessible between collection and validation:
- **HTTP 451** - Legally blocked (DMCA, court order)
- **Deleted** - Owner deleted the repository
- **Private** - Changed from public to private

**Q: Can I use fewer than 6 tokens?**  
A: Yes, but collection will be slower. Minimum 1 token required. Each token adds 10,000 req/hr capacity (5k GraphQL + 5k REST).

**Q: Why is `data/seattle_projects_*.json` so large?**  
A: Contains full metadata for 450k+ repositories (~260MB). Not committed to Git. Only generated/processed locally and during GitHub Actions deployment.

**Q: How do I add more GitHub tokens?**  
A:
1. Generate tokens at https://github.com/settings/tokens
2. Required scopes: `public_repo` (read public repositories)
3. Add to `.env.tokens` as `GITHUB_TOKEN_7`, `GITHUB_TOKEN_8`, etc.
4. Update `TokenManager` to support more tokens if needed

**Q: What happens if I switch Git branches?**  
A: Local-only files (`.env.tokens`, `data/seattle_projects_*.json`, `frontend/public/pages/`) **persist across branch switches** - they are never committed to Git, so they stay on your machine.

**Q: Should I commit the generated frontend files?**  
A: **No**. Frontend data files are regenerated during deployment. Only commit:
- `data/seattle_users_*.json` (small user metadata)
- `data/seattle_pypi_projects.json` (PyPI list)
- `data/pypi_official_packages.json` (official packages)
- `README.md` (documentation)

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

Made with ❤️ for Seattle's tech community

</div>
