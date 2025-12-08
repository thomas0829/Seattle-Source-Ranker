# Component Specification: Seattle Source Ranker

## 1. Software Components

### Component 1: Data Collector

**Purpose**: Systematically collect GitHub user and repository data from the Seattle area using distributed parallel processing.

**Inputs**:
- GitHub Personal Access Tokens (6 tokens for rate limit optimization)
- Search parameters:
  - Location filters (76 pre-optimized GraphQL queries)
  - Quality filters (repository count + follower count thresholds)
  - Batch size and worker configuration (8 workers × 2 concurrency)
  
**Outputs**:
- `data/seattle_users.json`: User metadata (committed to Git)
  ```json
  {
    "total_users": ~28000,
    "collected_at": "2025-12-07T02:25:22.634530-08:00",
    "query_strategy": "graphql multi-filter",
    "filters_used": 76,
    "usernames": ["user1", "user2", ...]
  }
  ```
- `data/seattle_projects.json`: Repository metadata (local only, not in Git)
  ```json
  {
    "total_projects": 432498,
    "total_stars": 2847621,
    "checked_users": 28283,
    "successful_users": 23456,
    "filtered_users": 4827,
    "projects": [
      {
        "name_with_owner": "owner/repo",
        "name": "repo",
        "owner": "username",
        "stars": 1500,
        "forks": 200,
        "language": "Python",
        "created_at": "2020-01-01T00:00:00Z",
        "pushed_at": "2024-12-01T10:00:00Z"
        // ... more fields
      }
    ]
  }
  ```

**Key Functions**:
- `DistributedCollector.collect_users()`: GraphQL-based user discovery with Union Types
- `fetch_users_batch_task()`: Celery task for parallel repository collection
- `get_token_manager().get_token()`: Intelligent token rotation
- `TokenManager._check_token_rate_limit()`: Monitor API usage

**Technologies**: Celery, Redis, GraphQL API v4, REST API v3, Python requests

---

### Component 2: PyPI Package Detector

**Purpose**: Identify which GitHub Python projects are published on PyPI to award bonus scores for production-ready packages.

**Inputs**:
- `data/pypi_official_packages.json`: Cache of 700K+ PyPI package names
- `data/top_pypi_packages.json`: Top 15,000 most-downloaded PyPI packages  
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
- `data/seattle_pypi_projects.json`: Detected PyPI packages (committed to Git)
  ```json
  {
    "total_python_projects": 54123,
    "pypi_projects": 1074,
    "detection_rate": "1.98%",
    "projects": [
      {
        "name": "requests",
        "owner": "psf",
        "stars": 51000,
        "on_pypi": true
        // ... more fields
      }
    ]
  }
  ```

- `data/seattle_top_pypi_matches.json`: Top 15k Global PyPI packages (committed to Git)
  ```json
  {
    "total_matches": 28,
    "top_15k_rate": "~0.05-0.1%",
    "matched_projects": [
      {
        "name": "facenet-pytorch",
        "repo": "timesler/facenet-pytorch",
        "stars": 5071,
        "on_top_pypi": true
        // ... more fields
      }
    ]
  }
  ```

**Key Functions**:
- `PyPIChecker.check_project(project)`: Determine if single project is on PyPI
- `PyPIChecker.load_or_download_index()`: Load/refresh PyPI package cache
- `PyPIChecker._normalize_name(name)`: Name normalization for matching
- `PyPIChecker._has_strong_signals(project)`: Validate using topics/description
- `generate_pypi_projects.py`: Main script to generate both output files

**Matching Strategies**:
1. Direct name match: `project-name` → `project-name` (case-insensitive)
2. Prefix removal: `python-requests` → `requests`, `py-test` → `test`
3. Separator normalization: `my_package` ↔ `my-package`
4. Manual mappings: `beautifulsoup` → `beautifulsoup4`, `opencv` → `opencv-python`
5. Exclusion patterns: `awesome-*`, `*-tutorial`, `*-demo`, generic names
6. Signal verification: Topics (pypi, python-package), description keywords

**Technologies**: Python requests library, JSON parsing, regex, offline caching

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
- SSR Score (0-1,000,000 range):
  ```python
  {
    "project_name": "example-project",
    "ssr_score": 724532,  # After PyPI bonus if applicable
    "score_breakdown": {
      "base_score": 687645,
      "pypi_multiplier": 1.05,  # Tier 1 bonus if on PyPI
      "top_pypi_multiplier": 1.10  # Tier 2 bonus if in Top 15k
    }
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
) × 1,000,000

Final Score (Python projects only):
- Not on PyPI:       Base Score × 1.0
- On PyPI (Tier 1):  Base Score × 1.05 (+5%)
- Top 15k (Tier 2):  Base Score × 1.05 × 1.10 = × 1.155 (+15.5%)

Tiered PyPI Bonuses:
- Tier 1 (Any PyPI): ×1.05 multiplier (~1K+ packages, ~2-3%)
- Tier 2 (Top 15k Global): ×1.10 additional multiplier (~30 packages, ~0.05-0.1%)
- Combined: ×1.155 total bonus for Top 15k packages
```

**Key Functions**:
- `calculate_github_score(project)`: Main scoring function in src/seattle_source_ranker/scoring.py
- `age_factor(created_at)`: Project maturity curve (peak at 3-5 years)
- `activity_factor(pushed_at, created_at)`: Recent maintenance scoring
- `health_factor(open_issues, stars)`: Issue management quality
- `log_normalize(value, base)`: Logarithmic scaling for distribution
- Frontend applies PyPI bonuses during data generation

**Technologies**: Python math library, datetime with timezone handling, zoneinfo

---

### Component 4: Secondary Validation & Enrichment

**Purpose**: Validate repository data integrity and enrich with accurate watchers count after initial collection.

**Inputs**:
- `data/seattle_projects_YYYYMMDD_HHMMSS.json`: Timestamped project data from initial collection
- GitHub API access via Token Manager
- Redis server for Celery task queue

**Outputs**:
- `data/seattle_projects.json`: Final validated and enriched project data
  ```json
  {
    "total_projects": 432498,  // After removing invalid repos
    "total_stars": 2847621,   // Recalculated after filtering
    "validated_repos": 427671,
    "removed_repos": 4827,
    "removal_reasons": {
      "deleted": 3000,
      "private": 1500,
      "blocked_451": 500
    },
    "projects": [
      {
        "name": "project",
        "owner": "user",
        "stars": 1500,
        "forks": 200,
        "watchers": 85,  // Real subscribers, not duplicate of stars
        "validated": true
        // ... more fields
      }
    ]
  }
  ```

**Key Functions**:
- `update_watchers_batch_task()`: Celery task for parallel validation
- `validate_repository()`: Check if repo is accessible (not deleted/private/blocked)
- `fetch_real_watchers()`: Get actual subscribers_count from GitHub API
- `filter_invalid_repos()`: Remove repositories that fail validation
- `recalculate_statistics()`: Update totals after filtering

**Validation Process**:
1. **Accessibility Check**: Verify repository still exists and is public
2. **HTTP 451 Detection**: Remove legally blocked repositories
3. **Watchers Update**: Replace star-duplicate with real subscribers_count
4. **Statistical Recalculation**: Update total_projects, total_stars after filtering
5. **Distributed Processing**: Use 8 workers × 2 concurrency for speed

**Performance**:
- **Single-threaded**: 5 hours for 432K repositories
- **8 Workers (distributed)**: 30-40 minutes
- **Speedup**: 7.5× faster with parallel processing

**Error Handling**:
- **404 Not Found**: Mark as deleted, remove from dataset
- **403 Forbidden**: Check if private or blocked, remove if inaccessible
- **451 Unavailable (Legal)**: Remove blocked repositories
- **Rate Limiting**: Automatic token rotation via Token Manager

**Technologies**: Celery, Redis, Python requests, GitHub REST API

---

### Component 5: Frontend Data Generator

**Purpose**: Transform validated data into optimized JSON files for web interface consumption.

**Inputs**:
- `data/seattle_projects.json`: Validated and enriched project data (from Secondary Validation)
- `data/seattle_pypi_projects.json`: PyPI detection results
- `data/seattle_top_pypi_matches.json`: Top 15k PyPI matches

**Outputs**:
- Paginated project files (generated locally, not in Git):
  - `frontend/public/pages/overall/page_1.json` through `page_~173.json` (50 projects each)
  - `frontend/public/pages/python/page_1.json` through `page_~109.json`
  - Each file contains 50 projects
  
- Metadata file:
  ```json
  {
    "total_projects": 432498,
    "total_pages": 200,
    "projects_per_page": 50,
    "last_updated": "2025-12-07T02:25:22-08:00",
    "languages": {
      "Python": 54123,
      "JavaScript": 89456
      // ... more languages
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

### Component 6: Token Manager

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

### Component 7: Web Interface (React Frontend)

**Purpose**: Provide interactive, user-friendly interface for exploring Seattle projects with advanced search, filtering, and visualization features.

**Inputs**:
- Paginated JSON files from Frontend Data Generator
- Metadata file with statistics and language counts
- PyPI project data for badge display
- Owner index files for autocomplete
- User interactions (search, filter, pagination, navigation)

**Outputs**:
- Five interactive web pages:
  1. **Home Page**: Project overview and navigation
  2. **Overall Rankings**: Top 10K projects with multi-language filtering
  3. **Python Rankings**: Python-specific rankings with PyPI badges
  4. **Scoring Methodology**: SSR algorithm explanation
  5. **Data Validation**: Quality assurance documentation

**Key Features**:

1. **Advanced Search System**:
   - Real-time autocomplete with debounce (300ms)
   - Owner suggestions (👤 icon) from pre-loaded indices
   - Topic suggestions (🏷️ icon) from project metadata
   - Keyboard navigation (arrow keys + Enter)
   - Search state persisted in URL parameters
   - Owner filtering mode for viewing all projects by specific user

2. **Filtering and Navigation**:
   - Multi-select language filter (Overall Rankings)
   - "Show All" / "Show Selected Languages" toggle
   - Page-based navigation (Previous/Next/Jump to Page)
   - URL state preservation for sharing filtered views
   - Browser back/forward support

3. **Data Visualization**:
   - SSR Score bars (relative to min/max per language)
   - Animated PyPI badges:
     * Rainbow gradient (regular PyPI, 4s animation)
     * Luxury gold-purple gradient (Top 15k, glow effects)
   - Language tags and topic chips
   - Hover tooltips with project details
   - Star/Fork/Watcher counts with icons

4. **Performance Optimizations**:
   - Client-side page caching (50 projects/page)
   - Lazy loading of paginated data
   - Owner index pre-loading (a-z + other groups)
   - Session storage for scroll position
   - Debounced search to reduce re-renders
   - Row animations and table flash effects

5. **User Experience**:
   - Glass morphism design with backdrop blur
   - Responsive layout (mobile + desktop)
   - Smooth scroll restoration on refresh (F5)
   - Visual feedback (hover states, loading indicators)
   - Accessible (ARIA labels, keyboard support)
   - Direct GitHub links (repository + owner profile)

**React Components**:
- `App.js`: Main router with 5 routes, GitHub source link
- `HomePage.js`: Landing page with overview cards
- `OverallRankingsPage.js`: Main rankings with language filters (~1687 lines)
  - Multi-language selection
  - Owner/topic search with suggestions
  - Pagination with caching
  - URL state management
- `PythonRankingsPage.js`: Python-specific rankings (~1029 lines)
  - PyPI badge display (rainbow + luxury)
  - Search and owner filtering
  - PyPI data integration
- `ScoringPage.js`: Algorithm documentation (~411 lines)
- `ValidationPage.js`: Data quality metrics (~479 lines)

**State Management**:
- URL Parameters: `?page=1&search=owner&langs=JavaScript,Python`
- Session Storage: Scroll positions for each page
- Local State: Page cache, search suggestions, filters
- React Hooks: `useState`, `useEffect`, `useRef`, `useSearchParams`

**Technologies**: 
- React 18+ with Hooks
- React Router v6 (URL-based navigation)
- CSS3 (glass morphism, gradients, animations)
- GitHub Pages (static hosting)
- Vanilla JavaScript (no external UI libraries)

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
│  - PyPIChecker loads package cache (707k)       │
│  - Matches Python projects (54k checked)        │
│  - Identifies 1,071 PyPI packages (2.74%)       │
│  - Matches 28 Top 15k global packages (0.07%)   │
└────────┬────────────────────────────────────────┘
         │ Outputs: seattle_pypi_projects.json
         │          seattle_top_pypi_matches.json
         ▼
┌─────────────────────────────────────────────────┐
│  4. SSR Scoring Engine (Component 3)            │
│  - Calculates base scores (0-1M range)          │
│  - Applies tiered PyPI bonuses:                 │
│    • ×1.05 for any PyPI (1,071 packages)        │
│    • ×1.10 additional for Top 15k (28 packages) │
│  - Sorts by score (highest first)               │
└────────┬────────────────────────────────────────┘
         │ Scored projects data
         ▼
┌─────────────────────────────────────────────────┐
│  5. Frontend Data Generator (Component 4)       │
│  - Creates ~200 overall ranking pages           │
│  - Creates ~782 Python ranking pages            │
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
        │  - Load 707k package cache             │
        │  - Check 54k Python projects           │
        │  - Detect 1,071 PyPI packages          │
        │  - Match 28 Top 15k global packages    │
        └────────────┬───────────────────────────┘
                     │
                     │ seattle_pypi_projects.json
                     │ seattle_top_pypi_matches.json
                     ▼
        ┌────────────────────────────────────────┐
        │   Component 3: SSR Scoring Engine      │
        │  - Calculate base scores (0-1M range)  │
        │  - Apply tiered PyPI bonuses:          │
        │    • ×1.05 (any PyPI)                  │
        │    • ×1.10 (Top 15k, total ×1.155)     │
        │  - Sort by score descending            │
        └────────────┬───────────────────────────┘
                     │
                     │ Scored project data
                     ▼
        ┌────────────────────────────────────────┐
        │   Component 4: Frontend Data Gen       │
        │  - Create ~200 overall pages           │
        │  - Create ~782 Python pages            │
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
- **Multi-Platform Support**: Extend data collection to GitLab, Bitbucket, and other open-source platforms
- **User Authentication System**: Implement login functionality for personalized features
- **Project Watchlist**: Allow users to save and track projects of interest
- Add historical trend tracking (score changes over time)

### Medium-term (6-12 months)
- **User Dashboard**: Personal project collections with custom tags and notes
- **Email Notifications**: Alerts for watched project updates and releases
- **Geographic Expansion**: Add more cities (Portland, Vancouver BC, San Francisco)
- Machine learning for project categorization
- Contributor network graph visualization

### Long-term (1+ years)
- **Backend Database Integration**: PostgreSQL/MongoDB for user data persistence
- **Advanced Filtering**: Custom queries and saved search filters
- **Collaboration Features**: Share project collections and recommendations
- Real-time updates instead of daily batch processing
- Community voting and curation features
- API endpoint for programmatic access
