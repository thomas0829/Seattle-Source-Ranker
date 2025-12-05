# Component Specification: Seattle Source Ranker

## 1. Software Components

### Component 1: Data Collector

**Purpose**: Systematically collect GitHub user and repository data from the Seattle area using distributed parallel processing.

**Inputs**:
- GitHub Personal Access Tokens (6 tokens for rate limit optimization)
- Search parameters:
  - Location filters (Seattle, Bellevue, Redmond, etc.)
  - Quality filters (follower count, repository count thresholds)
  - Batch size and worker configuration
  
**Outputs**:
- `seattle_users_YYYYMMDD_HHMMSS.json`: User metadata
  ```json
  {
    "total_users": 28256,
    "collected_at": "2025-12-02T09:30:38",
    "usernames": ["user1", "user2", ...]
  }
  ```
- `seattle_projects_YYYYMMDD_HHMMSS.json`: Repository metadata
  ```json
  {
    "total_projects": 457212,
    "total_stars": 2476436,
    "projects": [
      {
        "name": "project-name",
        "owner": "username",
        "stars": 1500,
        "forks": 200,
        "language": "Python",
        "created_at": "2020-01-01T00:00:00Z",
        ...
      }
    ]
  }
  ```

**Key Functions**:
- `DistributedCollector.collect_users()`: GraphQL-based user discovery
- `fetch_users_batch_task()`: Celery task for parallel repository collection
- `TokenManager.get_token()`: Intelligent token rotation
- `TokenManager.check_rate_limit()`: Monitor API usage

**Technologies**: Celery, Redis, GraphQL, REST API

---

### Component 2: PyPI Package Detector

**Purpose**: Identify which GitHub Python projects are published on PyPI to award bonus scores for production-ready packages.

**Inputs**:
- `pypi_official_packages.json`: Cache of 702,223 PyPI package names
- Python projects from Data Collector:
  ```python
  {
    "name": "requests",
    "language": "Python",
    "topics": ["http", "python"],
    "description": "Python HTTP library"
  }
  ```

**Outputs**:
- `seattle_pypi_projects.json`: Detected PyPI packages
  ```json
  {
    "total_python_projects": 55432,
    "pypi_projects": 10019,
    "detection_rate": "18.09%",
    "projects": [
      {
        "name": "requests",
        "owner": "psf",
        "stars": 51000,
        "on_pypi": true,
        ...
      }
    ]
  }
  ```
- Boolean classification for each Python project (on PyPI / not on PyPI)

**Key Functions**:
- `PyPIChecker.check_project(project)`: Determine if single project is on PyPI
- `PyPIChecker.batch_check(projects)`: Efficient batch checking
- `PyPIChecker._normalize_name(name)`: Name normalization for matching
- `PyPIChecker._has_strong_signals(project)`: Validate using topics/description

**Matching Strategies**:
1. Direct name match: `project-name` → `project-name`
2. Prefix removal: `python-requests` → `requests`
3. Separator normalization: `my_package` ↔ `my-package`
4. Manual mappings: `beautifulsoup` → `beautifulsoup4`
5. Exclusion patterns: `awesome-*`, `*-tutorial`, `*-demo`

**Technologies**: Python requests library, JSON parsing, regex

---

### Component 3: SSR Scoring Engine

**Purpose**: Rank projects using multi-factor algorithm that balances popularity, quality, and maintenance activity.

**Inputs**:
- Project metadata from Data Collector:
  ```python
  {
    "stars": 1500,
    "forks": 200,
    "watchers": 80,
    "open_issues": 25,
    "created_at": "2020-06-15T00:00:00Z",
    "pushed_at": "2024-11-20T10:30:00Z"
  }
  ```
- PyPI status from PyPI Detector (for Python projects)

**Outputs**:
- SSR Score (0-10,000 range):
  ```python
  {
    "project_name": "example-project",
    "ssr_score": 7245.32,
    "score_breakdown": {
      "stars_score": 2800,
      "forks_score": 1400,
      "watchers_score": 700,
      "age_score": 900,
      "activity_score": 1000,
      "health_score": 445.32
    },
    "pypi_bonus": 1.1  # 10% multiplier for Python+PyPI
  }
  ```

**Scoring Formula**:
```
Base Score = (
    log₁₀(stars + 1) / log₁₀(100000) × 0.40 +
    log₁₀(forks + 1) / log₁₀(10000) × 0.20 +
    log₁₀(watchers + 1) / log₁₀(10000) × 0.10 +
    age_factor(created_at) × 0.10 +
    activity_factor(pushed_at) × 0.10 +
    health_factor(open_issues, stars) × 0.10
) × 10000

Final Score = Base Score × 1.1  (if Python + on PyPI)
            = Base Score × 1.0  (otherwise)
```

**Key Functions**:
- `calculate_github_score(project)`: Main scoring function
- `age_factor(created_at)`: Project maturity scoring (peak at 3-5 years)
- `activity_factor(pushed_at, created_at)`: Recent maintenance scoring
- `health_factor(open_issues, stars)`: Issue management quality
- `log_normalize(value, base)`: Logarithmic scaling for distribution

**Technologies**: Python math library, datetime handling

---

### Component 4: Frontend Data Generator

**Purpose**: Transform collected data into optimized JSON files for web interface consumption.

**Inputs**:
- `seattle_projects_YYYYMMDD_HHMMSS.json`: Raw project data
- `seattle_pypi_projects.json`: PyPI detection results

**Outputs**:
- Paginated project files:
  - `frontend/public/pages/overall_page_1.json` through `page_200.json`
  - `frontend/public/pages/python_page_1.json` through `page_50.json`
  - Each file contains 50 projects
  
- Metadata file:
  ```json
  {
    "total_projects": 457212,
    "total_pages": 200,
    "projects_per_page": 50,
    "last_updated": "2025-12-02T09:30:38",
    "languages": {
      "Python": 55432,
      "JavaScript": 89234,
      ...
    }
  }
  ```

- Search index files:
  - `frontend/public/owner_index/a.json` through `z.json`
  - Alphabetically organized for autocomplete

**Key Functions**:
- `generate_paginated_files()`: Create page JSON files
- `classify_language(language)`: Categorize into 11 language groups
- `create_search_indices()`: Build owner and topic indices
- `generate_metadata()`: Create statistics summary

**Technologies**: Python JSON, pandas (optional), file I/O

---

### Component 5: Token Manager

**Purpose**: Manage multiple GitHub API tokens to maximize rate limits and ensure uninterrupted data collection.

**Inputs**:
- `.env.tokens` file or environment variables:
  ```
  GITHUB_TOKEN_1=ghp_xxxxx
  GITHUB_TOKEN_2=ghp_xxxxx
  ...
  GITHUB_TOKEN_6=ghp_xxxxx
  ```

**Outputs**:
- Active token for API requests
- Rate limit status for each token:
  ```python
  {
    "token": "ghp_xxxxx...",
    "remaining": 4850,
    "limit": 5000,
    "reset": "2025-12-04T20:30:00Z"
  }
  ```

**Key Functions**:
- `TokenManager.__init__()`: Load tokens from environment
- `get_token()`: Return token with highest remaining quota
- `rotate_token()`: Switch to next token in rotation
- `check_rate_limit()`: Query GitHub API for current limits
- `_cache_rate_limit()`: Cache limits for 60 seconds to reduce API calls

**Strategies**:
- **Automatic Selection**: Always use token with most remaining requests
- **Failover**: If token exhausted, rotate to next available
- **Cache**: Avoid excessive rate limit checks (60-second cache)
- **Thread-Safe**: Lock-based concurrency control for multi-worker scenarios

**Technologies**: Python os/environ, threading.Lock, requests library

---

### Component 6: Web Interface (React Frontend)

**Purpose**: Provide interactive, user-friendly interface for exploring Seattle projects.

**Inputs**:
- Paginated JSON files from Frontend Data Generator
- User interactions (search, filter, pagination)

**Outputs**:
- Rendered web pages with:
  - Project listings with SSR scores
  - Search and filter controls
  - Pagination controls
  - Direct links to GitHub repositories

**Key Features**:
- **Homepage**: Statistics overview, navigation
- **Overall Rankings**: All 457k projects, multi-language filtering
- **Python Rankings**: Python-specific view with PyPI badges
- **Scoring Page**: Algorithm explanation and methodology
- **Validation Page**: Data quality metrics

**Components**:
- `HomePage.js`: Landing page with statistics
- `OverallRankingsPage.js`: Main rankings interface
- `PythonRankingsPage.js`: Python-specific rankings
- `ScoringPage.js`: Algorithm documentation
- `ValidationPage.js`: Data quality information

**Technologies**: React, React Router, CSS (Glass Morphism design)

---

## 2. Component Interactions

### Use Case: Technical Recruiter Searching for Python Developers

**Scenario**: Jessica wants to find Python developers with PyPI packages.

**Component Interaction Flow**:

```
┌─────────────────┐
│  1. Web Browser │
│  (User Jessica) │
└────────┬────────┘
         │ HTTP Request: /python-rankings
         ▼
┌─────────────────────────────────────────────────┐
│  2. GitHub Pages (Static Hosting)               │
│  - Serves index.html                            │
│  - Loads React application                      │
└────────┬────────────────────────────────────────┘
         │ React Router activates PythonRankingsPage
         ▼
┌─────────────────────────────────────────────────┐
│  3. React Frontend (Component 6)                │
│  - PythonRankingsPage.js renders                │
│  - Fetches /pages/python_page_1.json            │
└────────┬────────────────────────────────────────┘
         │ AJAX Request: GET /pages/python_page_1.json
         ▼
┌─────────────────────────────────────────────────┐
│  4. Frontend Data Generator Output              │
│  - Serves pre-generated JSON file               │
│  - Contains 50 Python projects with scores      │
└────────┬────────────────────────────────────────┘
         │ Returns JSON with SSR scores
         ▼
┌─────────────────────────────────────────────────┐
│  5. React Frontend (Display)                    │
│  - Renders project list                         │
│  - Applies PyPI badge filter                    │
│  - Displays SSR scores                          │
└────────┬────────────────────────────────────────┘
         │ User searches "machine learning"
         ▼
┌─────────────────────────────────────────────────┐
│  6. React Frontend (Search)                     │
│  - Client-side filtering of loaded data         │
│  - Fetches /owner_index/m.json for suggestions  │
│  - Updates display with matching projects       │
└────────┬────────────────────────────────────────┘
         │ User clicks project link
         ▼
┌─────────────────────────────────────────────────┐
│  7. GitHub Repository                           │
│  - User redirected to GitHub project page       │
│  - Views code, contributions, owner profile     │
└─────────────────────────────────────────────────┘
```

**Behind the Scenes (Daily Automated Update)**:

```
Midnight Seattle Time
         │
         ▼
┌─────────────────────────────────────────────────┐
│  1. GitHub Actions Workflow                     │
│  - Triggered by cron schedule (08:00 UTC)       │
│  - Starts collection process                    │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  2. Data Collector (Component 1)                │
│  - TokenManager (Component 5) loads 6 tokens    │
│  - DistributedCollector starts Celery workers   │
│  - Collects users via GraphQL (28k users)       │
│  - Fetches repositories via REST (457k projects)│
└────────┬────────────────────────────────────────┘
         │ Outputs: seattle_users_*.json
         │          seattle_projects_*.json
         ▼
┌─────────────────────────────────────────────────┐
│  3. PyPI Package Detector (Component 2)         │
│  - PyPIChecker loads package cache (702k)       │
│  - Matches Python projects (55k checked)        │
│  - Identifies 10k PyPI packages (18%)           │
└────────┬────────────────────────────────────────┘
         │ Outputs: seattle_pypi_projects.json
         ▼
┌─────────────────────────────────────────────────┐
│  4. SSR Scoring Engine (Component 3)            │
│  - Calculates scores for all projects           │
│  - Applies 1.1× bonus to Python+PyPI projects   │
│  - Sorts by score (highest first)               │
└────────┬────────────────────────────────────────┘
         │ Scored projects data
         ▼
┌─────────────────────────────────────────────────┐
│  5. Frontend Data Generator (Component 4)       │
│  - Creates 200 overall ranking pages            │
│  - Creates 50 Python ranking pages              │
│  - Generates owner/topic search indices         │
│  - Updates metadata.json                        │
└────────┬────────────────────────────────────────┘
         │ Outputs: frontend/public/pages/*.json
         ▼
┌─────────────────────────────────────────────────┐
│  6. GitHub Actions Deployment                   │
│  - Commits updated JSON files                   │
│  - Pushes to gh-pages branch                    │
│  - Updates README.md statistics                 │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  7. GitHub Pages                                │
│  - Serves updated website                       │
│  - Users see fresh data                         │
└─────────────────────────────────────────────────┘
```

---

## 3. Preliminary Plan

### Priority Tasks (in order of implementation)

#### Phase 1: Core Infrastructure (Completed)
1. **Set up project structure** - src/, test/, examples/, doc/ organization
2. **Implement Token Manager** - Multi-token rotation with rate limit handling
3. **Build Data Collector** - GraphQL user discovery + REST repository fetching
4. **Add Celery workers** - Distributed parallel processing (8 workers × 2 concurrency)
5. **Create test suite** - pytest with 91+ passing tests

#### Phase 2: Data Processing (Completed)
6. **Develop SSR Scoring Algorithm** - Multi-factor scoring with logarithmic scaling
7. **Build PyPI Package Detector** - Offline matching with 702k package cache
8. **Implement PyPI bonus scoring** - 10% multiplier for Python packages on PyPI
9. **Create Frontend Data Generator** - Paginated JSON files for web interface
10. **Add secondary update script** - Validate and update watcher counts

#### Phase 3: Web Interface (Completed)
11. **Design React frontend** - Glass morphism UI with modern aesthetics
12. **Implement Overall Rankings page** - All projects with language filtering
13. **Implement Python Rankings page** - Python-specific view with PyPI badges
14. **Add search functionality** - Debounced search with autocomplete
15. **Create documentation pages** - Scoring methodology and validation info

#### Phase 4: Automation (Completed)
16. **Set up GitHub Actions** - Daily automated collection at midnight Seattle time
17. **Implement README auto-update** - Statistics refresh with each collection
18. **Add failure recovery** - Rollback mechanisms for failed collections
19. **Optimize performance** - Batch processing, caching, and rate limit optimization
20. **Deploy to GitHub Pages** - Static site hosting with custom domain support

#### Phase 5: Refinement & Documentation (Current)
21. **Write Functional Specification** - User profiles, use cases, data sources [DONE]
22. **Write Component Specification** - Software components, interactions, plan [DONE]
23. **Create usage examples** - examples/ directory with 3 demonstrative scripts [DONE]
24. **Comprehensive testing** - 91 passing tests with 8.75+ code quality score [DONE]
25. **Performance optimization** - 15-20 minute collection time for 30k users [DONE]

---

## 4. Technology Stack

### Backend (Python 3.11+)
- **Celery**: Distributed task queue for parallel processing
- **Redis**: Message broker for Celery workers
- **Requests**: HTTP library for GitHub API calls
- **pytest**: Testing framework (91+ tests)
- **pylint**: Code quality checking (8.75+/10 score)

### Frontend
- **React**: UI framework
- **React Router**: Client-side routing
- **CSS3**: Glass morphism design system

### Infrastructure
- **GitHub Actions**: CI/CD pipeline
- **GitHub Pages**: Static site hosting
- **Git**: Version control

### APIs
- **GitHub GraphQL API**: User discovery (5000 req/hr per token)
- **GitHub REST API**: Repository metadata (5000 req/hr per token)
- **PyPI JSON API**: Package name verification

---

## 5. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DAILY AUTOMATED WORKFLOW                  │
│                       (Midnight Seattle Time)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────────┐
        │     GitHub Actions Trigger             │
        │  - Cron: 0 8 * * * (08:00 UTC)        │
        │  - Setup: Python 3.11, Redis, tokens  │
        └────────────┬───────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────────┐
        │   Component 1: Data Collector          │
        │  ┌──────────────────────────────────┐  │
        │  │ Component 5: Token Manager       │  │
        │  │ - Load 6 GitHub tokens           │  │
        │  │ - Rotate based on rate limits    │  │
        │  └──────────────────────────────────┘  │
        │  - GraphQL: Discover 28k users         │
        │  - REST: Fetch 457k repositories       │
        │  - Celery: 8 workers × 2 concurrency   │
        └────────────┬───────────────────────────┘
                     │
                     │ seattle_users_*.json
                     │ seattle_projects_*.json
                     ▼
        ┌────────────────────────────────────────┐
        │   Component 2: PyPI Detector           │
        │  - Load 702k package cache             │
        │  - Check 55k Python projects           │
        │  - Detect 10k PyPI packages            │
        └────────────┬───────────────────────────┘
                     │
                     │ seattle_pypi_projects.json
                     ▼
        ┌────────────────────────────────────────┐
        │   Component 3: SSR Scoring Engine      │
        │  - Calculate scores for all projects   │
        │  - Apply PyPI bonus (1.1×)             │
        │  - Sort by score descending            │
        └────────────┬───────────────────────────┘
                     │
                     │ Scored project data
                     ▼
        ┌────────────────────────────────────────┐
        │   Component 4: Frontend Data Gen       │
        │  - Create 200 overall pages            │
        │  - Create 50 Python pages              │
        │  - Generate search indices             │
        │  - Update metadata.json                │
        └────────────┬───────────────────────────┘
                     │
                     │ frontend/public/pages/*.json
                     ▼
        ┌────────────────────────────────────────┐
        │      GitHub Actions Deploy             │
        │  - Update README statistics            │
        │  - Commit to gh-pages                  │
        │  - Push to GitHub                      │
        └────────────┬───────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────────┐
        │       Component 6: Web Interface       │
        │  - GitHub Pages serves static site     │
        │  - React app loads paginated data      │
        │  - Users interact with rankings        │
        └────────────────────────────────────────┘
```

---

## 6. Error Handling & Recovery

### Data Collection Failures
- **Rate Limit Exceeded**: Automatic token rotation to next available
- **Network Errors**: Retry with exponential backoff (3 attempts)
- **Invalid User Data**: Skip user and log warning, continue collection
- **Worker Crashes**: Celery automatically restarts failed tasks

### PyPI Detection Issues
- **Cache Missing**: Download fresh package list from PyPI (fallback)
- **Ambiguous Matches**: Use strict rules to avoid false positives
- **Network Timeout**: Retry with longer timeout, skip if still fails

### Frontend Generation Problems
- **Invalid JSON**: Validate data before writing, log errors
- **Disk Space**: Check available space before generation
- **File Write Errors**: Atomic writes with temp files and rename

### Deployment Failures
- **Build Errors**: Keep previous version live, alert via GitHub Actions
- **Push Rejected**: Force push with backup of previous state
- **GitHub Pages Down**: No action needed, auto-recovers when service resumes

---

## 7. Future Enhancements

### Short-term (Next 3 months)
- Add more cities (Portland, Vancouver BC, San Francisco)
- Implement historical trend tracking (score changes over time)
- Add email notifications for featured projects

### Medium-term (6-12 months)
- Machine learning for project categorization
- Contributor network graph visualization
- API endpoint for programmatic access

### Long-term (1+ years)
- Support for non-GitHub platforms (GitLab, Bitbucket)
- Real-time updates instead of daily batch processing
- Community voting and curation features

---

**Document Version**: 1.0  
**Last Updated**: December 4, 2025  
**Authors**: Seattle Source Ranker Team
