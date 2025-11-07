# Multi-Token Setup Guide

## Overview

Seattle-Source-Ranker supports multi-token rotation to bypass GitHub API rate limits. With multiple tokens, you can significantly increase collection throughput and handle large-scale data collection efficiently.

---

## System Components

### 1. TokenManager (`utils/token_manager.py`)
- Automatically loads multiple tokens from `.env.tokens`
- Thread-safe round-robin rotation
- Supports environment variables and configuration files
- Dynamic token selection based on rate limit status

### 2. Collection Worker (`distributed/workers/collection_worker.py`)
- Uses REST API with token rotation
- Automatic fallback when tokens are rate-limited
- Individual repo API calls for topics collection
- 8 workers × 2 concurrency = 16 parallel tasks

### 3. Distributed Collector (`distributed/distributed_collector.py`)
- Batch processing with Celery + Redis
- Automatic worker management
- Progress monitoring and retry logic
- Support for large-scale collections (481,323+ projects)

### 4. Worker Startup Script (`scripts/start_workers.sh`)
- Automatically loads all tokens from `.env.tokens`
- Passes tokens to all workers
- Creates logs in project root directory

---

## Performance Gains

### Single Token
- API Limit: 5,000 requests/hour
- Collection Speed: ~50 users/minute
- Large collection (30,000 users): ~10 hours

### 3 Tokens (Recommended)
- API Limit: 15,000 requests/hour (3× improvement)
- Collection Speed: ~150 users/minute
- Large collection (30,000 users): **~3.5 hours** ✅
- Suitable for GitHub Actions (6-hour limit)

### Real Performance (481,323 Projects)
- Workers: 8 workers × 2 concurrency
- Users Processed: 28,111
- Total Time: ~12 hours
- Success Rate: 99.98%
- Data Generated: 9,632 paginated JSON files

---

## Setup Instructions

### 1. Create Token Configuration File

Create `.env.tokens` in the project root:

```bash
# .env.tokens
GITHUB_TOKEN_1=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_TOKEN_2=ghp_yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
GITHUB_TOKEN_3=ghp_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
```

**Important**: This file is already in `.gitignore` and won't be committed to Git.

### 2. Generate GitHub Tokens

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Set scopes: `public_repo`, `read:user`
4. Copy token and add to `.env.tokens`
5. Repeat for each additional token (use different GitHub accounts if needed)

### 3. Verify Token Setup

```bash
# Count configured tokens
grep -c "^GITHUB_TOKEN_[0-9]=" .env.tokens
# Should show: 3 (or your configured number)

# Test token rotation
python3 test_token_rotation.py
```

---

## Usage Examples

### Small-Scale Test (100 projects)

```bash
# 1. Start Redis
redis-server --daemonize yes

# 2. Start workers (auto-loads tokens)
bash scripts/start_workers.sh

# 3. Collect 100 projects
python3 distributed/distributed_collector.py --target 100 --max-users 50 --batch-size 10
```

### Medium Collection (10,000 projects)

```bash
python3 distributed/distributed_collector.py \
    --target 10000 \
    --max-users 1000 \
    --batch-size 10
```

### Large Collection (100,000+ projects)

```bash
python3 distributed/distributed_collector.py \
    --target 1000000 \
    --max-users 30000 \
    --batch-size 10
```

### Generate Frontend Data

After collection completes:

```bash
python3 scripts/generate_frontend_data.py
```

This creates 9,632+ paginated JSON files in `frontend/public/pages/`

---

## Monitoring & Management

### Check Worker Status

```bash
# View active workers
ps aux | grep celery

# Check worker logs
tail -f logs/worker1.log
tail -f logs/worker*.log  # All workers
```

### Monitor Collection Progress

The collector shows real-time progress:
- ✅ Completed batches
- 📊 Total projects collected
- ⏱️ Elapsed time and ETA
- 🔄 Success/failure rates

### Stop Workers

```bash
bash scripts/stop_workers.sh
# or
pkill -f 'celery.*collection_worker'
```

---

## Troubleshooting

### Tokens Not Loading

```bash
# Check file permissions
ls -la .env.tokens

# Manually test
export $(grep -v '^#' .env.tokens | xargs)
echo $GITHUB_TOKEN_1
```

### Workers Can't Find Tokens

```bash
# Ensure correct directory
cd /home/thomas/Seattle-Source-Ranker
bash scripts/start_workers.sh
```

### Rate Limit Issues

- Each token has independent rate limit (5,000/hour)
- 3 tokens = 15,000 requests/hour total
- System automatically waits when all tokens are rate-limited
- Consider adding more tokens or increasing delays

### Worker Errors

```bash
# View detailed logs
tail -f logs/worker1.log

# Restart workers
bash scripts/stop_workers.sh
bash scripts/start_workers.sh
```

### Redis Connection Issues

```bash
# Check Redis status
redis-cli ping
# Should return: PONG

# Restart Redis
sudo systemctl restart redis
```

---

## Advanced Configuration

### Adjust Worker Count

Edit `scripts/start_workers.sh` to change number of workers (default: 8)

### Change Concurrency

Edit worker startup commands:
```bash
--concurrency=2  # Change to 3, 4, etc.
```

### Optimize Delays

Edit `distributed/workers/collection_worker.py`:
```python
time.sleep(0.05)  # Adjust between requests (default: 50ms)
```

---

## Best Practices

1. **Start Small**: Test with 100-1000 projects before large collections
2. **Monitor Logs**: Watch for errors or rate limit warnings
3. **Backup Data**: Collection data is saved incrementally
4. **Use Multiple Tokens**: 3+ tokens recommended for large collections
5. **Be Patient**: Large collections (100K+ projects) take hours
6. **Check Disk Space**: 481K projects ≈ 260MB raw data + frontend files

---

## System Requirements

- Python 3.11+
- Redis 6.0+
- 8GB+ RAM (for large collections)
- 5GB+ disk space
- Stable internet connection
- Multiple GitHub accounts (for multiple tokens)

---

## Additional Resources

- [Main README](README.md) - Complete project documentation
- [User Stories](docs/USER_STORIES.md) - Use cases and scenarios
- [GitHub API Documentation](https://docs.github.com/en/rest) - REST API reference

---

**🎉 Your multi-token system is ready to collect Seattle's open-source ecosystem!**
