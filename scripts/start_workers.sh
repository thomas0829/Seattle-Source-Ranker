#!/bin/bash
# Script to start Celery workers in background with multi-token support

echo "🚀 Starting Celery workers with multi-token rotation..."

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

# Activate conda environment (if exists)
if [ -f ~/anaconda3/etc/profile.d/conda.sh ]; then
    source ~/anaconda3/etc/profile.d/conda.sh
    conda activate ssr 2>/dev/null || echo "⚠️  Using system Python"
fi

# Load tokens from .env.tokens file
if [ -f .env.tokens ]; then
    echo "✅ Loading tokens from .env.tokens..."
    export $(grep -v '^#' .env.tokens | xargs)
    
    # Count tokens
    TOKEN_COUNT=$(grep -c "^GITHUB_TOKEN_[0-9]=" .env.tokens)
    echo "✅ Loaded $TOKEN_COUNT GitHub tokens"
else
    # Fallback to single GITHUB_TOKEN
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "⚠️  No .env.tokens file found and GITHUB_TOKEN not set!"
        echo "   Please configure .env.tokens or set GITHUB_TOKEN"
        exit 1
    fi
    echo "⚠️  Using single GITHUB_TOKEN (for better performance, configure .env.tokens)"
    export GITHUB_TOKEN
fi

# Set PYTHONPATH to project root so workers can import utils/
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Create logs directory in project root
mkdir -p "$PROJECT_ROOT/logs"

# Change to distributed directory for worker imports
cd distributed

# Start 8 workers in background
GITHUB_TOKEN=$GITHUB_TOKEN nohup python3 -m celery -A workers.collection_worker worker \
    --loglevel=info --concurrency=2 -n worker1@%h \
    > "$PROJECT_ROOT/logs/worker1.log" 2>&1 &
echo "✅ Worker 1 started (PID: $!)"

GITHUB_TOKEN=$GITHUB_TOKEN nohup python3 -m celery -A workers.collection_worker worker \
    --loglevel=info --concurrency=2 -n worker2@%h \
    > "$PROJECT_ROOT/logs/worker2.log" 2>&1 &
echo "✅ Worker 2 started (PID: $!)"

GITHUB_TOKEN=$GITHUB_TOKEN nohup python3 -m celery -A workers.collection_worker worker \
    --loglevel=info --concurrency=2 -n worker3@%h \
    > "$PROJECT_ROOT/logs/worker3.log" 2>&1 &
echo "✅ Worker 3 started (PID: $!)"

GITHUB_TOKEN=$GITHUB_TOKEN nohup python3 -m celery -A workers.collection_worker worker \
    --loglevel=info --concurrency=2 -n worker4@%h \
    > "$PROJECT_ROOT/logs/worker4.log" 2>&1 &
echo "✅ Worker 4 started (PID: $!)"

GITHUB_TOKEN=$GITHUB_TOKEN nohup python3 -m celery -A workers.collection_worker worker \
    --loglevel=info --concurrency=2 -n worker5@%h \
    > "$PROJECT_ROOT/logs/worker5.log" 2>&1 &
echo "✅ Worker 5 started (PID: $!)"

GITHUB_TOKEN=$GITHUB_TOKEN nohup python3 -m celery -A workers.collection_worker worker \
    --loglevel=info --concurrency=2 -n worker6@%h \
    > "$PROJECT_ROOT/logs/worker6.log" 2>&1 &
echo "✅ Worker 6 started (PID: $!)"

GITHUB_TOKEN=$GITHUB_TOKEN nohup python3 -m celery -A workers.collection_worker worker \
    --loglevel=info --concurrency=2 -n worker7@%h \
    > "$PROJECT_ROOT/logs/worker7.log" 2>&1 &
echo "✅ Worker 7 started (PID: $!)"

GITHUB_TOKEN=$GITHUB_TOKEN nohup python3 -m celery -A workers.collection_worker worker \
    --loglevel=info --concurrency=2 -n worker8@%h \
    > "$PROJECT_ROOT/logs/worker8.log" 2>&1 &
echo "✅ Worker 8 started (PID: $!)"

echo ""
echo "📊 Workers started successfully!"
echo "   Total: 8 workers × 2 concurrency = 16 parallel tasks"
echo "   View logs: tail -f $PROJECT_ROOT/logs/worker*.log"
echo "   Stop all: pkill -f 'celery.*collection_worker'"
echo "   Monitor: python3 monitor_celery.py"
