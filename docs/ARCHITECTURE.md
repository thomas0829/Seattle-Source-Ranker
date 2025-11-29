# Detailed Project Architecture

## System Components

### 1. Data Collection Layer (`distributed/`)
- **distributed_collector.py** (1136 lines): Main coordinator
  - GraphQL Search API for user discovery (76 pre-optimized filters)
  - **GraphQL Union Types**: Handles both User and Organization accounts
  - REST Core API for project data collection
  - Intelligent rate limit handling with token rotation
  - Seattle timezone consistency (America/Los_Angeles)
  
- **collection_worker.py**: Celery workers for parallel processing
  - 8 workers × 2 concurrency = 16 parallel tasks
  - Individual repo API calls for detailed metadata
  - Topics and tech stack collection
  
- **token_manager.py**: Multi-token rotation system
  - 6 Personal Access Tokens for rate limit optimization
  - Requires `read:org` scope for organization data
  - 30,000 requests/hour total capacity
  - Automatic failover and recovery

### 2. PyPI Integration Layer (`utils/`)
- **pypi_checker.py** (~250 lines): Package detection system
  - **Offline matching** for high performance (<30 seconds for 55k projects)
  - **Zero false positives**: 100% precision via strict matching rules
  - Local cache of 702,223 PyPI packages
  - Multiple matching strategies:
    * Direct name match
    * Underscore/hyphen conversion
    * Prefix removal (python-, py-, django-, flask-, pytest-)
    * Manual mappings for known edge cases
  - Signal verification:
    * Topic checking (pypi, python-package, pip)
    * Description analysis (pip install mentions)
    * Generic name filtering (chat, bot, api, etc.)
  
- **generate_pypi_projects.py**: PyPI project list generator
  - Processes all Python projects (~55k)
  - Outputs `seattle_pypi_projects.json` (~10k packages, ~3MB)
  - Detection rate: ~18% of Python projects are on PyPI
  - Sorted by stars (most popular first)

### 3. Analysis Layer
- **ranker.py**: SSR scoring algorithm implementation
  - Multi-factor weighted scoring
  - Logarithmic scaling for distribution
  - Language-based classification
  
- **analyzer.py**: Statistical analysis
  - Data quality metrics
  - Distribution analysis
  - Performance benchmarks

### 4. Testing Layer (`test/`)
- **pytest test suite** (15 tests, all passing)
  - `test_graphql_queries.py`: Organization fragment validation
  - `test_update_readme.py`: README update logic
  - `test_classify_languages.py`: Language classification
  - `test_pypi_50_projects.py`: PyPI checker accuracy validation
- **pytest.ini**: Configuration to avoid ROS plugin conflicts
- **run_tests.sh**: Test execution wrapper

### 5. Frontend Layer (`frontend/`)
Built with React, featuring:
- **Dual ranking pages**:
  - Overall Rankings: All languages with multi-select filtering
  - Python Rankings: Python-specific with PyPI integration bonus
- Real-time search with debounce and owner/topic suggestions
- Paginated view (50 projects/page)
- Lazy loading for performance
- Animated PyPI badge with rainbow gradient
- Slate blue theme with sky accents
- Tech stack visualization

### 6. Automation Layer (`.github/workflows/`)
- **collect-and-deploy.yml**: Daily automated workflow
  - Scheduled: Midnight Seattle time (08:00 UTC)
  - Full collection → PyPI detection → Ranking → Verification → Deploy
  - Automatic README updates with latest stats
  - Commits user data and PyPI data to Git
  - Failure protection with rollback
  - Old data cleanup

## Performance Metrics

### Collection Speed
- **Single-threaded baseline**: ~2 hours for 10K users
- **Distributed (8 workers)**: ~15-20 minutes for 30K users
- **Performance gain**: 5-7.5× faster
- **Throughput**: ~25-30 users/second with full project data

### API Rate Limits
- **GraphQL Search API**: 5,000 requests/hour/token
  - User discovery with complex queries
  - 76 pre-optimized filters for Seattle area
  
- **REST Core API**: 5,000 requests/hour/token
  - Detailed project metadata
  - Topics and tech stack information

### Data Scale
- **464,133 projects** tracked
- **2,817,581 total stars** analyzed
- **28,203 verified accounts** in Seattle area (users + organizations)
- **55,034 Python projects** identified
- **9,962 PyPI packages** detected (18.10% of Python projects)
- **702,223 PyPI packages** indexed for offline matching
- **252MB** primary data file (local only, not in Git)
- **3MB** PyPI projects data (in Git)
- **12MB** PyPI packages index (in Git)
- **9,632 paginated files** for frontend (50 projects each)

### PyPI Detection Performance
- **Processing time**: <30 seconds for 55,034 Python projects
- **Accuracy**: 100% precision (zero false positives)
- **Detection rate**: 18.10% of Python projects are on PyPI
- **Matching strategies**: 5 methods (direct, underscore/dash conversion, prefix removal, manual mapping, signal verification)
- **Cache duration**: 7 days for PyPI index

## Data Pipeline Flow

```
1. User Discovery (GraphQL Search API)
   ↓ 76 pre-optimized location filters
   ↓ GraphQL Union Types (User + Organization)
   ↓ ~30,000 potential accounts
   
2. User Verification (REST API)
   ↓ Location confirmation
   ↓ Organization support (allenai, awslabs, FredHutch, etc.)
   ↓ ~28,000 verified Seattle accounts
   
3. Project Collection (REST API)
   ↓ All public repositories
   ↓ Topics & tech stack metadata
   ↓ ~464,000 projects
   
4. PyPI Detection (Offline Matching)
   ↓ Load 702k PyPI packages index
   ↓ Filter ~55,000 Python projects
   ↓ Strict matching with signal verification
   ↓ ~10,000 packages detected (18% detection rate)
   ↓ Zero false positives (100% precision)
   
5. Multi-factor Scoring (SSR Algorithm)
   ↓ 6-dimension analysis
   ↓ Logarithmic scaling
   ↓ Ranked output
   
6. Language Classification
   ↓ 11 major language categories
   ↓ Separate ranking per language
   
7. Frontend Generation
   ↓ Pagination (50/page)
   ↓ JSON file splitting
   ↓ ~9,600 paginated files
   
8. Deployment & Git Commit
   ↓ GitHub Pages deployment
   ↓ Commit user data (seattle_users_*.json)
   ↓ Commit PyPI data (seattle_pypi_projects.json, pypi_official_packages.json)
   ↓ Update README statistics
   ↓ Automatic daily updates
```

## Scoring Algorithm Details

### SSR (Seattle Source Ranker) Formula

```python
def calculate_ssr_score(repo):
    # Base metrics (70% weight)
    stars_score = log(stars + 1) * 0.40
    forks_score = log(forks + 1) * 0.20
    watchers_score = log(watchers + 1) * 0.10
    
    # Quality factors (30% weight)
    age_score = calculate_age_maturity(created_at) * 0.10
    activity_score = calculate_recent_activity(updated_at) * 0.10
    health_score = calculate_repo_health(issues, pull_requests) * 0.10
    
    return (stars_score + forks_score + watchers_score + 
            age_score + activity_score + health_score)
```

### Age Maturity Curve
- **0-1 year**: 0.3-0.5 (new projects)
- **1-3 years**: 0.5-0.9 (growing)
- **3-5 years**: 0.9-1.0 (mature, peak score)
- **5+ years**: 0.8-0.9 (established, slight decay)

### Activity Score
- Updated within 6 months: 1.0
- 6-12 months: 0.8
- 1-2 years: 0.5
- 2+ years: 0.3

### Health Metrics
- Open issues ratio
- Pull request merge rate
- Response time to issues
- Contribution frequency

## Configuration Files

### `.env.tokens`
```bash
GITHUB_TOKEN_1=ghp_xxx...
GITHUB_TOKEN_2=ghp_xxx...
# ... up to GITHUB_TOKEN_6
```

### `.github/workflows/collect-and-deploy.yml`
- Cron schedule: `0 8 * * *` (midnight Seattle time)
- Secrets: GITHUB_TOKEN_1 through GITHUB_TOKEN_6
- **Token requirements**: Must have `read:org` scope for organization data
- Environment: TZ=America/Los_Angeles
- Failure protection with `.collection_success` marker
- **Workflow steps**:
  1. Checkout code
  2. Set up Python 3.11
  3. Install dependencies
  4. Run distributed collection (up to 30K users)
  5. Verify collection (check for allenai organization)
  6. Clean temporary files
  7. Update README with latest stats
  8. **Generate PyPI projects list** (new step)
  9. Generate frontend paginated data
  10. Build and deploy frontend to GitHub Pages
  11. **Commit user data and PyPI data to Git** (updated)
  12. Display summary with PyPI statistics

### Redis Configuration
```bash
docker run -d \
  --name ssr-redis \
  -p 6379:6379 \
  redis:7-alpine
```

## Development Workflow

1. **Local Development**
   ```bash
   # Start Redis
   docker start ssr-redis
   
   # Activate conda environment
   conda activate ssr
   
   # Run tests
   cd test && ./run_tests.sh
   
   # Test PyPI detection
   python3 scripts/generate_pypi_projects.py
   
   # Test full workflow
   ./scripts/test_workflow.sh
   ```

2. **GitHub Actions**
   - Triggered daily at midnight Seattle time
   - Manual trigger via Actions tab
   - Automatic deployment on success
   - **New**: PyPI detection runs after collection

3. **Data Updates**
   - Collection runs automatically
   - **PyPI detection** identifies packages on PyPI
   - README stats updated post-collection
   - Frontend rebuilt with new data
   - **User data and PyPI data** committed to main branch
   - Website deployed to gh-pages

4. **Testing**
   ```bash
   # Run all tests
   pytest
   
   # Run specific test
   pytest test/test_pypi_50_projects.py -v
   
   # Run with coverage
   pytest --cov --cov-report=html
   ```

## Troubleshooting Guide

### Common Issues

**Redis Connection Error**
```bash
docker ps  # Check if ssr-redis is running
docker start ssr-redis  # Start if stopped
```

**Token Rate Limit**
```python
# Check token status
from utils.token_manager import TokenManager
tm = TokenManager()
for token in tm.tokens:
    print(f"Token: {token[:10]}... Rate: {tm.get_rate_limit(token)}")
```

**Collection Failures**
- Check `.collection_success` marker exists
- Review workflow logs in GitHub Actions
- Verify all 6 tokens are valid in Secrets
- Ensure Redis is accessible

**Frontend Build Issues**
```bash
cd frontend
npm install  # Reinstall dependencies
npm run build  # Rebuild
```

## Technology Stack

### Backend
- **Python 3.11** with Conda environment
- **Celery** for distributed task queue
- **Redis** for message broker
- **Requests** for GitHub API calls
- **zoneinfo** for timezone handling

### Frontend
- **React** for UI framework
- **CSS3** with glass morphism design
- **GitHub Pages** for hosting
- Vanilla JavaScript for lightweight performance

### DevOps
- **GitHub Actions** for CI/CD
- **Docker** for Redis containerization
- **Git LFS** for large data files (optional)
