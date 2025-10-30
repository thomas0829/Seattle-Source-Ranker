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

### Incremental Collection

1. **Load Existing Data** - Reads `seattle_projects_10000.json`
2. **Deduplication** - Uses `name_with_owner` as unique key
3. **Smart Refresh** - Only updates stale projects
4. **Intelligent Replace** - Better projects replace lower-scored ones

### Replacement Strategies

- `lowest_stars` - Replace projects with fewest stars (default)
- `oldest` - Replace least recently updated projects
- `lowest_activity` - Replace by activity score (stars + forks + watchers)

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

## Performance

| Operation | Time | API Calls |
|-----------|------|-----------|
| View status | <1s | 0 |
| Refresh 100 projects | ~2 min | ~100 |
| Refresh 1000 projects | ~15 min | ~1000 |
| Collect 10000 projects | ~5 min | ~1000 |

**Recommendations**:
- Daily: `--refresh --days 1` (fast)
- Weekly: `--full-update` (complete)

## License

MIT License - see [LICENSE](LICENSE)
