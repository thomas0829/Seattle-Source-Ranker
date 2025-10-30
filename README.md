# Seattle Source Ranker

A data-driven system to identify and rank influential software projects from Seattle-area developers.

## Features

- 🔍 **Smart Collection** - Collect 10,000+ Seattle projects from GitHub
- 📊 **Influence Scoring** - Calculate project influence using SSR algorithm
- 🔄 **Incremental Updates** - Smart refresh without re-fetching existing data
- 💾 **Data Persistence** - Automatic backup and versioning
- 🎯 **Language Analytics** - Rank projects by programming language

## Quick Start

### 1. Setup

```bash
# Clone repository
git clone https://github.com/thomas0829/Seattle-Source-Ranker.git
cd Seattle-Source-Ranker

# Install dependencies
pip install requests tqdm

# Set GitHub token
export GITHUB_TOKEN="your_github_token_here"
```

### 2. Collect Projects (First Time)

```bash
# Collect 10,000 Seattle projects
python3 -m collectors.collect_seattle_projects
```

This will:
- Search for Seattle developers on GitHub (sorted by followers)
- Fetch their public repositories
- Save to `data/seattle_projects_10000.json`
- Takes ~5 minutes

### 3. Check Status

```bash
python3 manage_projects.py --status
```

### 4. Daily/Weekly Maintenance

```bash
# Refresh stale data (weekly)
python3 manage_projects.py --full-update --target 10000

# Quick refresh (daily)
python3 manage_projects.py --refresh --days 1
```

## Project Structure

```
Seattle-Source-Ranker/
├── manage_projects.py            # CLI management tool
├── main.py                       # Original v1.0 script
│
├── collectors/                   # Data collection modules
│   ├── collect_seattle_projects.py
│   ├── incremental_collector.py
│   ├── github_client.py
│   ├── graphql_client.py
│   └── cursor_manager.py
│
├── analysis/                     # Analysis & scoring
│   ├── scoring.py
│   ├── analyzer.py
│   ├── ranker.py
│   ├── api.py
│   └── models.py
│
├── utils/                        # Utilities
│   ├── pypi_client.py
│   ├── classify_languages.py
│   ├── update_with_pypi.py
│   ├── celery_config.py
│   ├── fetch_worker.py
│   └── score_worker.py
│
├── verification/                 # Location verification
│   ├── verifier.py
│   └── verifier_serpapi.py
│
├── data/                         # Project database
│   ├── seattle_projects_10000.json
│   └── seattle_projects_10000_metadata.json
│
└── frontend/                     # React visualization
```

## Usage

### View Current Status

```bash
python3 manage_projects.py --status
```

### Refresh Stale Data

```bash
# Refresh projects older than 7 days
python3 manage_projects.py --refresh --days 7
```

### Collect New Projects

```bash
# Add new projects up to 10,000
python3 manage_projects.py --collect-new --target 10000
```

### Full Update (Recommended)

```bash
# Refresh + collect new
python3 manage_projects.py --full-update --target 10000 --days 7
```

## How It Works

### Data Collection Strategy

**Two Collection Methods:**

#### 1. GraphQL API (Recommended for large-scale collection)
- **Breaks through 1,000 result limit** with cursor-based pagination
- Can collect unlimited results using `after` cursor
- More efficient - fetches all data in single query
- Supports checkpoint recovery for long-running operations
- Used by `graphql_client.py`

```python
from collectors.graphql_client import GitHubGraphQLClient

client = GitHubGraphQLClient()
repos = client.fetch_all_repositories(
    query="location:seattle stars:>10",
    max_results=10000
)
```

#### 2. REST API + User-Centric Approach (Alternative method)
- Search Seattle developers by location
- Fetch all repos from each developer
- Useful when you need detailed user information
- Used by `collect_seattle_projects.py`

**Why User-Centric?**
GitHub's REST search API has a 1,000 result limit per query. By searching developers first, we bypass this limit and can collect 10,000+ projects.

### GitHub API Usage

**Authentication:**
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

**Rate Limits:**
- GraphQL: 5,000 points/hour (queries cost different points)
- REST Authenticated: 5,000 requests/hour
- REST Unauthenticated: 60 requests/hour

**GraphQL Advantages:**
- Single query fetches all needed data
- Cursor-based pagination (no 1,000 limit)
- Efficient batch operations
- Built-in rate limit info in response

**REST API Endpoints (legacy/incremental updates):**
- `GET /search/users` - Find Seattle developers
- `GET /users/{username}/repos` - Fetch user's repositories
- `GET /repos/{owner}/{repo}` - Update project stats

**Smart Caching:**
- Owner locations cached in `data/owner_location_cache.json`
- Checkpoint recovery for GraphQL pagination
- Avoids redundant API calls for known developers
- Automatically saves on each update

### Incremental Collection System

1. **Load Existing Data** - Reads `seattle_projects_10000.json`
2. **Check Staleness** - Identifies projects older than N days
3. **Refresh Stale Projects** - Updates stats via GitHub API
4. **Collect New Projects** - Fills gaps up to target count
5. **Intelligent Replace** - Better projects replace lower-scored ones
6. **Auto Backup** - Creates `_backup.json` before updates

### Replacement Strategies

- `lowest_stars` - Replace projects with fewest stars (default)
- `oldest` - Replace least recently updated projects  
- `lowest_activity` - Replace by activity score (stars + forks + watchers)

### Scoring Algorithm

**GitHub Score Formula:**
```
Score = 0.4 × S_norm + 0.25 × F_norm + 0.15 × W_norm + 0.10 × T_age + 0.10 × H_health
```

**Components:**
- **S_norm**: Normalized stars (community popularity)
- **F_norm**: Normalized forks (community engagement)
- **W_norm**: Normalized watchers (long-term attention)
- **T_age**: Project age weight - `years / (years + 2)`
- **H_health**: Health score - `1 - (issues / (issues + 10))`

**Normalization:**
All values normalized against dataset maximum for fair comparison across different project scales.

## Python API

### Basic Usage

```python
from collectors.incremental_collector import IncrementalProjectCollector

# Initialize
collector = IncrementalProjectCollector()

# Check status
print(f"Projects: {len(collector.existing_projects)}")
```

### Refresh Data

```python
# Refresh projects older than 7 days
updated_count = collector.refresh_stale_projects(days_old=7)
```

### Add New Projects

```python
stats = collector.add_new_projects(
    new_projects,
    max_total=10000,
    replace_strategy="lowest_stars"
)
```

## Data Update Workflow

### Generate Frontend Data

After collecting or updating projects, regenerate the frontend data:

```bash
python3 generate_frontend_data.py
```

This will:
- Calculate scores using SSR algorithm
- Classify projects by language (Python, JavaScript, Go, etc.)
- Sort by score within each language category
- Generate `ranked_by_language_seattle.json` for frontend

### Deploy to GitHub Pages

```bash
cd frontend
npm run deploy
```

Updates the live website at: https://thomas0829.github.io/Seattle-Source-Ranker

## Performance

| Operation | Time | API Calls |
|-----------|------|-----------|
| View status | <1s | 0 |
| Refresh 100 projects | ~2 min | ~100 |
| Refresh 1000 projects | ~15 min | ~1000 |
| Collect 10000 projects | ~5 min | ~1000 |
| Generate frontend data | ~2s | 0 |
| Deploy to GitHub Pages | ~30s | 0 |

**Recommendations**:
- Daily: `--refresh --days 1` (fast, minimal API usage)
- Weekly: `--full-update` (complete, ~1000 API calls)
- After updates: Run `generate_frontend_data.py` + `npm run deploy`

## API Rate Limit Management

**Check Current Limit:**
```bash
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit
```

**If Rate Limited:**
- Wait 1 hour for reset
- Use multiple GitHub tokens (rotate)
- Reduce `--days` parameter for smaller updates

## Troubleshooting

### Update Failed?

```bash
# Restore from backup
cp data/seattle_projects_10000_backup.json data/seattle_projects_10000.json
```

### Rate Limit Hit?

GitHub API allows 5,000 requests/hour. Wait 1 hour or use multiple tokens.

### Frontend Not Updating?

```bash
# Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
# Or check if data was regenerated:
ls -lh frontend/build/ranked_by_language_seattle.json
```

## License

MIT License - see [LICENSE](LICENSE)
