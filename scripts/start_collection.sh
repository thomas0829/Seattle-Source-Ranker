#!/bin/bash
# Safe collection script with checkpoint and background execution
# Usage: ./start_collection.sh

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "🚀 Safe Distributed Collection Starter"
echo "=========================================="

# Activate conda environment
echo "📦 Activating conda environment..."
source ~/anaconda3/etc/profile.d/conda.sh
conda activate ssr

# Get date and timestamp
DATE=$(date +%Y%m%d)
TIMESTAMP=$(date +%H%M%S)

# Create logs directory with date
LOG_DIR="logs/${DATE}"
mkdir -p "${LOG_DIR}"

# Step 1: Clean up old data
echo ""
echo "🧹 Step 1: Cleaning up old data..."
echo "   Clearing Redis..."
redis-cli FLUSHDB
echo "   ✅ Redis cleared"

echo "   Note: Old logs are kept in logs/<date> directories"

# Step 2: Stop any running workers
echo ""
echo "🛑 Step 2: Stopping old workers..."
pkill -9 -f "celery.*worker" 2>/dev/null || true
sleep 2
WORKER_COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l)
if [ "$WORKER_COUNT" -eq 0 ]; then
    echo "   ✅ All workers stopped"
else
    echo "   ⚠️  Warning: $WORKER_COUNT workers still running"
fi

# Step 3: Start collection in background with nohup
echo ""
echo "🚀 Step 3: Starting collection in background..."
echo "   Parameters:"
echo "      - Max users: 30000"
echo "      - Batch size: 50"
echo "      - Workers: 8 (auto-managed)"
echo ""

LOG_FILE="${LOG_DIR}/collection_${TIMESTAMP}.log"

# Record start time
echo "Start time: $(date '+%Y-%m-%d %H:%M:%S')" | tee collection_time.log
date +%s > collection_start.txt

nohup python3 -u distributed/distributed_collector.py \
    --max-users 30000 \
    --batch-size 50 \
    --workers 8 \
    > "$LOG_FILE" 2>&1 &

COLLECTOR_PID=$!
echo "$COLLECTOR_PID" > collection.pid

echo "   ✅ Collection started!"
echo "   PID: $COLLECTOR_PID"
echo "   Log: $LOG_FILE"
echo ""

# Wait a few seconds and check if it's still running
sleep 5

if ps -p $COLLECTOR_PID > /dev/null; then
    echo "✅ Collection is running successfully!"
    echo ""
    echo "📊 To monitor progress:"
    echo "   tail -f $LOG_FILE"
    echo ""
    echo "🛑 To stop collection:"
    echo "   kill $COLLECTOR_PID"
    echo "   pkill -f distributed_collector"
    echo ""
    echo "Process ID saved to: .collection_pid"
    echo "$COLLECTOR_PID" > .collection_pid
else
    echo "❌ Collection failed to start!"
    echo "   Check log: $LOG_FILE"
    exit 1
fi

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Collection is now running in the background."
echo "It will continue even if you close this terminal."
echo ""
echo "Estimated time: 1-2 hours for 28,126 users"
