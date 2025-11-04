#!/bin/bash
# Script to start Celery workers in background

echo "🚀 Starting Celery workers in background..."

# Activate conda environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate ssr

# Set working directory
cd /home/thomas/Seattle-Source-Ranker

# Export GITHUB_TOKEN if not already set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  GITHUB_TOKEN not found in environment!"
    echo "   Please set it before starting workers:"
    echo "   export GITHUB_TOKEN='your_token_here'"
    exit 1
fi

echo "✅ GITHUB_TOKEN found"
export GITHUB_TOKEN

# Set PYTHONPATH to project root so workers can import utils/
export PYTHONPATH=/home/thomas/Seattle-Source-Ranker:$PYTHONPATH

# Create logs directory if not exists
mkdir -p distributed/logs

# Change to distributed directory for worker imports
cd distributed

# Start 3 workers in background
nohup python3 -m celery -A workers.collection_worker worker \
    --loglevel=info --concurrency=2 -n worker1@%h \
    > logs/worker1.log 2>&1 &
echo "✅ Worker 1 started (PID: $!)"

nohup python3 -m celery -A workers.collection_worker worker \
    --loglevel=info --concurrency=2 -n worker2@%h \
    > logs/worker2.log 2>&1 &
echo "✅ Worker 2 started (PID: $!)"

nohup python3 -m celery -A workers.collection_worker worker \
    --loglevel=info --concurrency=2 -n worker3@%h \
    > logs/worker3.log 2>&1 &
echo "✅ Worker 3 started (PID: $!)"

echo ""
echo "📊 Workers started successfully!"
echo "   View logs: tail -f logs/worker*.log"
echo "   Stop all: pkill -f 'celery.*collection_worker'"
echo "   Monitor: python3 monitor_celery.py"
