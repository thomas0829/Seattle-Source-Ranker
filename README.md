# Seattle Source Ranker

A distributed system for collecting and ranking influential open-source projects from Seattle-area developers using Celery + Redis workers.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Celery](https://img.shields.io/badge/celery-5.3+-green.svg)](https://docs.celeryproject.org/)

## Features

- **Distributed Collection** - Celery + Redis workers for parallel processing
- **High Performance** - Multiple workers processing batches concurrently
- **Influence Scoring** - SSR algorithm ranking by stars, forks, age, and health
- **GraphQL API** - Efficient data fetching from GitHub
- **JSON Output** - Clean, structured results for easy integration

## Architecture

```
Coordinator (distributed_collector.py)
    |
    v
Redis (Message Broker)
    |
    v
Celery Workers (3 workers, 2 concurrency each)
    |
    v
GitHub GraphQL API
```

## Quick Start

### 1. Install Dependencies

```bash
git clone https://github.com/thomas0829/Seattle-Source-Ranker.git
cd Seattle-Source-Ranker
pip install -r requirements.txt
```

### 2. Install Redis

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

### 3. Configure GitHub Token

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

Get a token at: https://github.com/settings/tokens

Required scopes: `public_repo`, `read:user`

### 4. Start Workers

```bash
bash distributed/start_workers.sh
```

Check status:
```bash
ps aux | grep celery
tail -f distributed/logs/worker*.log
```

### 5. Run Collection

Quick test (100 projects):
```bash
python3 distributed/distributed_collector.py --target 100 --max-users 50 --batch-size 10
```

Full collection (10,000 projects):
```bash
python3 distributed/distributed_collector.py --target 10000 --max-users 1000 --batch-size 10
```

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
bash distributed/start_workers.sh
```

Stop workers:
```bash
bash distributed/stop_workers.sh
```

Monitor with Flower:
```bash
celery -A distributed.workers.collection_worker flower --port=5555
```
Then open http://localhost:5555

## Performance

| Projects | Workers | Time | Speed vs Single-thread |
|----------|---------|------|------------------------|
| 100 | 3 | ~1 min | - |
| 1,000 | 3 | ~5 min | - |
| 10,000 | 3 | ~30 min | 5x |
| 100,000 | 5 | ~4 hours | 7.5x |

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

## Project Structure

```
Seattle-Source-Ranker/
├── distributed/
│   ├── distributed_collector.py   # Main coordinator
│   ├── workers/
│   │   └── collection_worker.py   # Celery worker tasks
│   ├── start_workers.sh           # Start workers
│   ├── stop_workers.sh            # Stop workers
│   └── logs/                      # Worker logs
├── collectors/
│   └── graphql_client.py          # GitHub GraphQL client
├── utils/
│   └── celery_config.py           # Celery config
├── data/                          # Output files
├── requirements.txt
└── README.md
```

## SSR Scoring Algorithm

Projects are ranked using the Seattle Source Ranker (SSR) algorithm:

```
Score = 0.4 × Stars + 0.25 × Forks + 0.15 × Watchers + 0.10 × Age + 0.10 × Health

Where:
  Stars    = Normalized star count (0-1)
  Forks    = Normalized fork count (0-1)
  Watchers = Normalized watcher count (0-1)
  Age      = Project age weight (older is better)
  Health   = Health score (fewer open issues is better)
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
tail -f distributed/logs/worker1.log
```

Restart workers:
```bash
bash distributed/stop_workers.sh
bash distributed/start_workers.sh
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- GitHub GraphQL API for efficient data fetching
- Celery for distributed task processing
- Redis for message brokering
- Seattle tech community

## Version History

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
