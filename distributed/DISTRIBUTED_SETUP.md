# 🚀 Distributed Collection Setup Guide

This guide shows how to run the Seattle-Source-Ranker in distributed mode with multiple Celery workers.

## 🏗️ Architecture

```
┌─────────────────────┐
│   Coordinator       │  ← You run this
│ distributed_collector.py │
└──────────┬──────────┘
           │
           ▼
    ┌─────────────┐
    │   Redis     │  ← Message broker
    │   Queue     │
    └──────┬──────┘
           │
    ┌──────┴──────┬──────────┬──────────┐
    ▼             ▼          ▼          ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ...
│Worker 1 │  │Worker 2 │  │Worker 3 │
│GraphQL  │  │GraphQL  │  │GraphQL  │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     └────────────┴────────────┘
                  │
                  ▼
          ┌──────────────┐
          │ PostgreSQL   │  ← Centralized storage
          └──────────────┘
```

## 📋 Prerequisites

1. **Docker & Docker Compose** (recommended) OR
2. **Local Redis + PostgreSQL** (manual setup)

## 🐳 Option A: Docker Compose (Recommended)

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your GitHub token
nano .env
```

Add to `.env`:
```bash
GITHUB_TOKEN=your_github_token_here
POSTGRES_PASSWORD=secure_password_here
```

### 2. Start Infrastructure

```bash
# Start Redis, PostgreSQL, and 3 workers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f worker1
```

### 3. Run Collection

```bash
# Install Python dependencies locally (for coordinator)
pip install -r requirements.txt

# Run distributed collection
python3 distributed_collector.py --target 10000 --max-users 1000 --batch-size 10

# Monitor workers in real-time
open http://localhost:5555  # Flower dashboard
```

### 4. Monitor Progress

```bash
# Watch worker logs
docker-compose logs -f worker1 worker2 worker3

# Check Flower dashboard
# http://localhost:5555

# Check Redis queue
docker-compose exec redis redis-cli
> LLEN celery
> KEYS *
```

### 5. Scale Workers

```bash
# Add more workers
docker-compose up -d --scale worker1=5

# Or manually in docker-compose.yml, add worker4, worker5, etc.
```

## 🛠️ Option B: Local Setup (Without Docker)

### 1. Install Dependencies

```bash
# Install Redis
sudo apt install redis-server  # Ubuntu/Debian
brew install redis             # macOS

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib  # Ubuntu/Debian
brew install postgresql                        # macOS

# Install Python packages
pip install -r requirements.txt
```

### 2. Start Services

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start PostgreSQL
sudo service postgresql start

# Create database
psql -U postgres
CREATE DATABASE seattle_source_ranker;
CREATE USER ssr_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE seattle_source_ranker TO ssr_user;
\q

# Initialize database schema
psql -U ssr_user -d seattle_source_ranker -f database/init.sql
```

### 3. Configure Environment

```bash
# Set environment variables
export GITHUB_TOKEN="your_github_token_here"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="seattle_source_ranker"
export POSTGRES_USER="ssr_user"
export POSTGRES_PASSWORD="your_password"
```

### 4. Start Workers

```bash
# Terminal 3: Worker 1
celery -A workers.collection_worker worker --loglevel=info --concurrency=2 -n worker1@%h

# Terminal 4: Worker 2
celery -A workers.collection_worker worker --loglevel=info --concurrency=2 -n worker2@%h

# Terminal 5: Worker 3
celery -A workers.collection_worker worker --loglevel=info --concurrency=2 -n worker3@%h

# Terminal 6: Flower (monitoring)
celery -A workers.collection_worker flower --port=5555
```

### 5. Run Collection

```bash
# Terminal 7: Coordinator
python3 distributed_collector.py --target 10000 --max-users 1000 --batch-size 10
```

## 📊 Performance Comparison

| Method | Workers | Time | Speed |
|--------|---------|------|-------|
| Single-threaded REST | 1 | ~15 min | 1x |
| Hybrid (local) | 1 | ~8 min | 1.9x |
| Distributed | 3 | ~3 min | 5x |
| Distributed | 5 | ~2 min | 7.5x |

## 🎯 Usage Examples

### Basic Collection
```bash
python3 distributed_collector.py --target 10000 --max-users 1000
```

### Custom Batch Size
```bash
# Smaller batches = more parallelism but more overhead
python3 distributed_collector.py --target 10000 --batch-size 5

# Larger batches = less overhead but less parallelism
python3 distributed_collector.py --target 10000 --batch-size 20
```

### Quick Test
```bash
# Test with 100 projects
python3 distributed_collector.py --target 100 --max-users 50 --batch-size 5
```

## 🔍 Monitoring

### Flower Dashboard
- URL: http://localhost:5555
- Shows: Active tasks, worker status, task history, stats

### Redis CLI
```bash
docker-compose exec redis redis-cli

# Check queue length
LLEN celery

# List all keys
KEYS *

# Get task info
GET celery-task-meta-<task-id>
```

### PostgreSQL
```bash
docker-compose exec postgres psql -U ssr_user -d seattle_source_ranker

# Check total repositories
SELECT COUNT(*) FROM repositories;

# Top repositories
SELECT * FROM top_repositories LIMIT 10;

# Collection tasks
SELECT * FROM collection_tasks ORDER BY started_at DESC;
```

## 🐛 Troubleshooting

### Workers Not Starting
```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# Check worker logs
docker-compose logs worker1

# Restart workers
docker-compose restart worker1 worker2 worker3
```

### Tasks Stuck in Queue
```bash
# Purge all tasks
celery -A workers.collection_worker purge

# Restart workers
docker-compose restart worker1 worker2 worker3
```

### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Check connection
docker-compose exec postgres psql -U ssr_user -d seattle_source_ranker -c "SELECT 1;"
```

## 🧹 Cleanup

```bash
# Stop all services
docker-compose down

# Remove data volumes (⚠️ deletes all data)
docker-compose down -v

# Remove Docker images
docker-compose down --rmi all
```

## 📈 Optimization Tips

1. **Adjust concurrency**: Change `--concurrency=2` to `--concurrency=4` for more parallel tasks per worker

2. **Batch size tuning**:
   - Small batches (5-10): Better for many workers, faster feedback
   - Large batches (20-50): Better for few workers, less overhead

3. **Worker count**:
   - Start with 3-5 workers
   - Monitor CPU/memory usage
   - Scale based on GitHub API rate limits (5000 requests/hour)

4. **Rate limit management**:
   - 3 workers = ~1500 requests/hour each
   - 5 workers = ~900 requests/hour each
   - Monitor via Flower dashboard

## 🎓 Next Steps

1. ✅ Test with small dataset (100 projects)
2. ✅ Scale to full dataset (10,000 projects)
3. ✅ Implement PostgreSQL persistence
4. ✅ Add monitoring and alerting
5. ✅ Optimize batch sizes and concurrency
6. ⬜ Add automatic retry logic
7. ⬜ Implement checkpoint recovery
8. ⬜ Deploy to production cluster
