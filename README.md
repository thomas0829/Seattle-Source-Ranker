# Seattle Source Ranker

A comprehensive system for discovering, collecting, and ranking influential open-source projects from Seattle-area developers. Features distributed collection with Celery + Redis workers and an interactive React-based web visualization.

🌐 **Live Website**: [https://thomas0829.github.io/Seattle-Source-Ranker/](https://thomas0829.github.io/Seattle-Source-Ranker/)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Celery](https://img.shields.io/badge/celery-5.3+-green.svg)](https://docs.celeryproject.org/)
[![React](https://img.shields.io/badge/react-18.0+-61dafb.svg)](https://reactjs.org/)

## 🌟 Features

### Data Collection
- **Distributed Processing** - Celery + Redis workers for parallel collection
- **High Performance** - 8 workers with 2 concurrency each (16 concurrent tasks)
- **Token Rotation** - Support for multiple GitHub tokens to avoid rate limits
- **GraphQL API** - Efficient data fetching from GitHub
- **Scalable** - Successfully collected 481,323 projects from 28,111 Seattle developers

### Ranking & Scoring
- **Weighted Scoring** - `Score = Stars × 0.6 + Forks × 0.3 + Watchers × 0.1`
- **Language Classification** - 11 major programming languages
- **Multi-factor Analysis** - Stars, forks, and watchers weighted by importance

### Web Visualization
- **Interactive React UI** - Modern, responsive web interface
- **Lazy Loading Pagination** - 50 projects per page, 9,632 total pages with page jump
- **Multi-select Filtering** - Checkbox-based language selection (11 languages + "All" option)
- **Real-time Search** - Instant filtering with 500ms debounce for optimal performance
- **Page Navigation** - Direct page jump input for quick access to any page
- **Tech Stack Display** - Project topics/technologies shown in hover details (when available)
- **Elegant Design** - Glass morphism UI with smooth animations and hover tooltips

## Architecture

```
Coordinator (distributed_collector.py)
    |
    v
Redis (Message Broker)
    |
    v
Celery Workers (8 workers, 2 concurrency each = 16 parallel tasks)
    |
    v
GitHub REST API (with topics collection)
```

## 🚀 Quick Start

### Option 1: View Existing Data (Recommended)

If you just want to explore the collected data:

```bash
# Clone the repository
git clone https://github.com/thomas0829/Seattle-Source-Ranker.git
cd Seattle-Source-Ranker

# Install frontend dependencies
cd frontend
npm install

# Start the web interface
npm start
```

Open http://localhost:3000/Seattle-Source-Ranker to browse 481,323 Seattle projects!

### Option 2: Run Your Own Collection

To collect fresh data from GitHub:

#### 1. Install Dependencies

```bash
git clone https://github.com/thomas0829/Seattle-Source-Ranker.git
cd Seattle-Source-Ranker
pip install -r requirements.txt
```

#### 2. Install Redis

Ubuntu/Debian:
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

macOS:
```bash
brew install redis
brew services start redis
```

#### 3. Configure GitHub Tokens

For best performance, use multiple tokens to avoid rate limits:

```bash
# Create token file
echo "GITHUB_TOKEN_1=ghp_your_token_1_here" > .env.tokens
echo "GITHUB_TOKEN_2=ghp_your_token_2_here" >> .env.tokens
echo "GITHUB_TOKEN_3=ghp_your_token_3_here" >> .env.tokens
```

Get tokens at: https://github.com/settings/tokens

Required scopes: `public_repo`, `read:user`

#### 4. Start Workers

```bash
bash scripts/start_workers.sh
```

Check status:
```bash
ps aux | grep celery
tail -f logs/worker*.log
```

#### 5. Run Collection

Quick test (100 projects):
```bash
python3 distributed/distributed_collector.py --target 100 --max-users 50 --batch-size 10
```

Large collection (recommended):
```bash
python3 distributed/distributed_collector.py --target 1000000 --max-users 30000 --batch-size 10
```

#### 6. Generate Frontend Data

After collection completes:

```bash
python3 scripts/generate_frontend_data.py
```

This creates paginated JSON files in `frontend/public/pages/`

## Usage

### Basic Command

```bash
python3 distributed/distributed_collector.py \
  --target 10000 \
  --max-users 1000 \
  --batch-size 10
```

### Parameters

- `--target`: Number of projects to collect (default: 10000)
- `--max-users`: Maximum users to search (default: 1000)
- `--batch-size`: Users per worker batch (default: 10)
- `--output`: Output file path (optional)

### Worker Management

Start workers:
```bash
bash scripts/start_workers.sh
```

Stop workers:
```bash
bash scripts/stop_workers.sh
```

Monitor with Flower:
```bash
celery -A distributed.workers.collection_worker flower --port=5555
```
Then open http://localhost:5555

## Performance

| Projects | Workers | Concurrency | Time | Success Rate |
|----------|---------|-------------|------|--------------|
| 30,000 | 8 | 2 each (16 total) | ~2 hours | 99.95% |
| 481,323 | 8 | 2 each (16 total) | ~12 hours | 99.98% |

**Latest Collection Stats (Nov 6, 2025):**
- Total Projects: **481,323**
- Total Stars: **2,801,313**
- Total Users: **28,111**
- Success Rate: **99.98%**
- Data Structure: **9,632 paginated JSON files**

## Output Format

Results are saved as JSON:

```json
{
  "total_projects": 10000,
  "total_stars": 1234567,
  "successful_users": 950,
  "failed_users": 50,
  "collected_at": "2025-11-04T12:34:56.789012",
  "projects": [
    {
      "name_with_owner": "microsoft/vscode",
      "name": "vscode",
      "description": "Visual Studio Code",
      "url": "https://github.com/microsoft/vscode",
      "stars": 150000,
      "forks": 25000,
      "watchers": 5000,
      "language": "TypeScript",
      "topics": ["typescript", "editor", "vscode", "electron"],
      "created_at": "2015-09-03T20:23:12Z",
      "updated_at": "2025-11-04T10:15:30Z",
      "pushed_at": "2025-11-04T08:45:22Z",
      "open_issues": 5000,
      "has_issues": true,
      "owner": {
        "login": "microsoft",
        "name": "Microsoft",
        "location": "Redmond, WA",
        "company": "Microsoft",
        "email": null,
        "bio": "Open source projects from Microsoft"
      }
    }
  ]
}
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | Yes | - |
| `REDIS_HOST` | Redis server host | No | localhost |
| `REDIS_PORT` | Redis server port | No | 6379 |

### Celery Configuration

Edit `utils/celery_config.py`:

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
```

## 📁 Project Structure

```
Seattle-Source-Ranker/
├── distributed/
│   ├── distributed_collector.py   # Main coordinator
│   └── workers/
│       └── collection_worker.py   # Celery worker tasks (REST API)
├── utils/
│   ├── celery_config.py           # Celery configuration
│   └── token_manager.py           # Multi-token rotation
├── scripts/
│   ├── generate_frontend_data.py  # Generate paginated data (enhanced SSR algorithm)
│   ├── start_workers.sh           # Start workers
│   ├── stop_workers.sh            # Stop workers
│   └── start_collection.sh        # Safe collection startup script
├── frontend/
│   ├── public/
│   │   ├── pages/                 # 9,632 paginated JSON files
│   │   └── metadata.json          # Language statistics
│   ├── src/
│   │   ├── App.js                 # React main component
│   │   └── App.css                # Styling
│   └── package.json
├── data/                          # Collection output files
│   ├── seattle_projects_10000.json
│   ├── seattle_projects_unlimited_*.json
│   └── seattle_users_*.json
├── docs/                          # Documentation
│   ├── MULTI_TOKEN_GUIDE.md       # Multi-token setup guide
│   └── USER_STORIES.md            # User scenarios
├── logs/                          # Worker logs
│   └── worker*.log
├── requirements.txt
├── LICENSE
└── README.md
```

## 📊 Enhanced SSR Scoring Algorithm

Projects are ranked using a comprehensive multi-factor scoring system:

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

### Why This Algorithm?

1. **Logarithmic Scaling** - Better distribution across projects of different sizes
2. **Age Maturity** - Rewards established projects (2-8 years), penalizes too new/old
3. **Recent Activity** - Prefers actively maintained projects
4. **Health Metrics** - Considers issue management quality
5. **Multi-dimensional** - Balances popularity with quality indicators

### Example Scores
- **Top Projects**: 5,000-8,000 points (high stars, active, mature)
- **Mid-range**: 1,000-3,000 points (moderate popularity, good health)
- **Small Projects**: 100-500 points (new or niche projects)
- **Inactive**: < 100 points (abandoned or minimal activity)

### Python Projects Enhancement
For Python projects, the system also considers:
- **PyPI Downloads** - Monthly download statistics via PyPI API
- **Package Popularity** - Integration with pypistats.org
- **Dependency Network** - Projects used as dependencies get bonus points

This comprehensive approach ensures fair ranking across different project types and sizes.

## 🎨 Frontend Visualization

The project includes a modern React-based web interface for exploring the data:

### Features
- **Paginated Browsing** - 50 projects per page with lazy loading
- **Multi-select Language Filter** - Checkbox-based filtering with "All" option (default)
  - 11 programming languages: JavaScript, Python, Java, C++, Ruby, Go, Rust, Swift, PHP, Kotlin, Other
  - Multiple language selection supported
  - Auto-uncheck "All" when selecting specific languages
- **Search Functionality** - Real-time search with 500ms debounce
  - Search by project name or owner
  - Searches top 20 pages per language (~1,000 projects per language)
  - Shows search scope hint
- **Page Jump** - Direct navigation input to jump to any page (1 to 9,632)
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Glass Morphism UI** - Modern, elegant design with smooth animations
- **Project Details** - Hover tooltips with comprehensive information:
  - Language
  - Tech Stack (topics - only shown when available)
  - Description
  - Stars, forks, and issues count
- **Direct Links** - Click to open projects on GitHub

### Running the Frontend

```bash
cd frontend
npm install
npm start
```

Open http://localhost:3000/Seattle-Source-Ranker

### Frontend Structure
```
frontend/
├── public/
│   ├── pages/              # Paginated JSON data
│   │   ├── javascript/     # 2,361 pages
│   │   ├── python/         # 1,146 pages
│   │   ├── java/           # 585 pages
│   │   └── ...
│   └── metadata.json       # Language statistics
├── src/
│   ├── App.js              # Main React component
│   └── App.css             # Styling
└── package.json
```

## Troubleshooting

### Workers Not Starting

Check Redis:
```bash
redis-cli ping
```

Check Python path:
```bash
echo $PYTHONPATH
```

Restart Redis:
```bash
sudo systemctl restart redis
```

### API Rate Limits

Check remaining requests:
```bash
curl -H "Authorization: bearer $GITHUB_TOKEN" \
  https://api.github.com/rate_limit
```

GitHub provides 5,000 requests per hour per token.

### Worker Errors

View logs:
```bash
tail -f logs/worker1.log
```

Restart workers:
```bash
bash scripts/stop_workers.sh
bash scripts/start_workers.sh
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **GitHub REST API** - Reliable data fetching with topics support
- **Celery & Redis** - Distributed task processing and message brokering
- **React** - Modern, interactive web interface
- **Seattle Tech Community** - 28,111 amazing developers and their 481,323 projects
- **Open Source Contributors** - Everyone who makes Seattle's tech scene vibrant

##  Additional Documentation

- [Multi-Token Guide](docs/MULTI_TOKEN_GUIDE.md) - How to configure and use multiple GitHub tokens for faster collection
- [User Stories](docs/USER_STORIES.md) - Real-world use cases and user scenarios

## 👥 Team & Responsibilities

This project is developed and maintained by a collaborative team:

### Team Members

| Member | Role | Responsibilities |
|--------|------|------------------|
| **ycl0829** | Project Architecture & System Design Lead | Project conceptualization, system architecture, technical infrastructure, project coordination |
| **Zouqs2** | Data Validation & Reliability Engineer | Validation methods design, data quality assurance, verification mechanisms, integrity testing |
| **muwenc** | Scoring Algorithm & Interpretability Specialist | Scoring methodology, ranking metrics interpretability, algorithm documentation, transparent scoring |
| **wszhao87** | Frontend Developer & UI/UX Designer | Web page implementation, UI/UX design, frontend development, user experience optimization |

## 📈 Project Statistics

### Data Distribution by Language
| Language | Projects | Percentage | Pages |
|----------|----------|------------|-------|
| Other | 212,704 | 44.2% | 4,255 |
| JavaScript | 118,025 | 24.5% | 2,361 |
| Python | 57,260 | 11.9% | 1,146 |
| Java | 29,247 | 6.1% | 585 |
| C++ | 21,349 | 4.4% | 427 |
| Ruby | 15,423 | 3.2% | 309 |
| Go | 8,266 | 1.7% | 166 |
| Rust | 5,976 | 1.2% | 120 |
| Swift | 5,689 | 1.2% | 114 |
| PHP | 5,369 | 1.1% | 108 |
| Kotlin | 2,015 | 0.4% | 41 |
| **Total** | **481,323** | **100%** | **9,632** |

## 🔄 Version History

### v3.0 (2025-11-06)
- **Major Collection Upgrade**: Collected 481,323 projects (16x increase from 30K to 481K)
- **API Migration**: Switched from GraphQL to REST API for better stability and reliability
- **Topics Collection**: Added GitHub topics/tech stack data collection
  - Individual repo API calls to fetch topics
  - Conditional display in frontend (only when topics exist)
  - ~10% of Seattle projects have topics configured
- **Enhanced Frontend Interactivity**:
  - Multi-select checkbox language filtering (replaces tab-based filtering)
  - "All" option with smart auto-uncheck behavior
  - Real-time search with 500ms debounce optimization
  - Page jump input for direct navigation to any page
  - Improved hover details with tech stack display
  - Three loading modes: All (mixed), Selected languages, Search
- **Enhanced SSR Algorithm**: Multi-factor scoring with 6 dimensions
  - Base metrics: Stars (40%), Forks (20%), Watchers (10%)
  - Quality factors: Age (10%), Activity (10%), Health (10%)
  - Logarithmic scaling for better distribution
  - Age maturity curve (peak at 3-5 years)
  - Recent activity weighting
  - Health metrics based on issue management
- **PyPI Integration**: Python projects enhanced with download statistics (infrastructure ready)
- **Lazy Loading Frontend**: Paginated system with 9,632 page files (50 projects each)
- **Enhanced UI**: Glass morphism design with elegant pagination buttons
- **Performance Optimization**: 8 workers with 16 concurrent tasks
- **Multi-token Support**: Token rotation system for rate limit handling
- **Language Classification**: 11 major programming languages
- **Project Cleanup**: Consolidated codebase, removed deprecated files

### v2.1 (2025-11-04)
- Implemented distributed collection system with Celery + Redis
- Added parallel batch processing with multiple workers
- Integrated GitHub GraphQL API for efficient data fetching
- Performance improvement: 5-7.5x faster than single-threaded
- Fixed authentication, import paths, and query handling
- Complete English documentation

### v2.0 (2024-10-30)
- SSR scoring algorithm implementation
- Multi-factor ranking system
- React frontend for visualization
- JSON data export

### v1.0 (2024-10-25)
- Initial release
- Basic GitHub REST API collection
- Seattle developer search
