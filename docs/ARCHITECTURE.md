# Detailed Project Architecture

## System Components

### 1. Data Collection Layer (`distributed/`)
- **distributed_collector.py** (1114 lines): Main coordinator
  - GraphQL Search API for user discovery (76 pre-optimized filters)
  - REST Core API for project data collection
  - Intelligent rate limit handling with token rotation
  - Seattle timezone consistency (America/Los_Angeles)
  
- **collection_worker.py**: Celery workers for parallel processing
  - 8 workers × 2 concurrency = 16 parallel tasks
  - Individual repo API calls for detailed metadata
  - Topics and tech stack collection
  
- **token_manager.py**: Multi-token rotation system
  - 6 Personal Access Tokens for rate limit optimization
  - 30,000 requests/hour total capacity
  - Automatic failover and recovery

### 2. Analysis Layer
- **ranker.py**: SSR scoring algorithm implementation
  - Multi-factor weighted scoring
  - Logarithmic scaling for distribution
  - Language-based classification
  
- **analyzer.py**: Statistical analysis
  - Data quality metrics
  - Distribution analysis
  - Performance benchmarks

### 3. Frontend Layer (`frontend/`)
Built with React, featuring:
- Multi-select language filtering
- Real-time search with debounce
- Paginated view (50 projects/page)
- Lazy loading for performance
- Glass morphism design
- Tech stack visualization

### 4. Automation Layer (`.github/workflows/`)
- **collect-and-deploy.yml**: Daily automated workflow
  - Scheduled: Midnight Seattle time (08:00 UTC)
  - Full collection → Ranking → Verification → Deploy
  - Automatic README updates with latest stats
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
- **447,533 projects** tracked
- **2,166,692 total stars** analyzed
- **23,371 verified users** in Seattle area
- **252MB** primary data file
- **9,632 paginated files** for frontend (50 projects each)

## Data Pipeline Flow

```
1. User Discovery (GraphQL Search API)
   ↓ 76 pre-optimized location filters
   ↓ ~30,000 potential users
   
2. User Verification (REST API)
   ↓ Location confirmation
   ↓ ~23,000 verified Seattle users
   
3. Project Collection (REST API)
   ↓ All public repositories
   ↓ Topics & tech stack metadata
   ↓ ~450,000 projects
   
4. Multi-factor Scoring (SSR Algorithm)
   ↓ 6-dimension analysis
   ↓ Logarithmic scaling
   ↓ Ranked output
   
5. Language Classification
   ↓ 11 major language categories
   ↓ Separate ranking per language
   
6. Frontend Generation
   ↓ Pagination (50/page)
   ↓ JSON file splitting
   ↓ ~9,600 paginated files
   
7. Deployment
   ↓ GitHub Pages
   ↓ Automatic updates
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
- Environment: TZ=America/Los_Angeles
- Failure protection with `.collection_success` marker

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
   
   # Test locally
   ./scripts/test_workflow.sh
   ```

2. **GitHub Actions**
   - Triggered daily at midnight Seattle time
   - Manual trigger via Actions tab
   - Automatic deployment on success

3. **Data Updates**
   - Collection runs automatically
   - README stats updated post-collection
   - Frontend rebuilt with new data
   - Changes committed to main branch
   - Website deployed to gh-pages

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
