#!/bin/bash
# Safe collection script with checkpoint and background execution
# Usage: ./start_collection_safe.sh

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🚀 Safe Distributed Collection Starter"
echo "=========================================="

# Activate conda environment
echo "📦 Activating conda environment..."
source ~/anaconda3/etc/profile.d/conda.sh
conda activate ssr

# Step 1: Clean up old data
echo ""
echo "🧹 Step 1: Cleaning up old data..."
echo "   Clearing Redis..."
redis-cli FLUSHDB
echo "   ✅ Redis cleared"

echo "   Archiving old logs..."
if [ -d "distributed/logs" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    ARCHIVE_DIR="distributed/logs_archive_${TIMESTAMP}"
    mkdir -p "$ARCHIVE_DIR"
    mv distributed/logs/worker_*.log "$ARCHIVE_DIR/" 2>/dev/null || true
    echo "   ✅ Logs archived to: $ARCHIVE_DIR"
fi

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
echo "   Using user file: data/seattle_users_20251106_020713.json"
echo "   Parameters:"
echo "      - Target: 1000000 projects (no limit)"
echo "      - Batch size: 50"
echo "      - Workers: 8"
echo "      - Max users: 28126 (from file)"
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="distributed/logs/collection_${TIMESTAMP}.log"
mkdir -p distributed/logs

nohup python3 -u distributed/distributed_collector.py \
    --target 1000000 \
    --batch-size 50 \
    --workers 8 \
    --max-users 28126 \
    > "$LOG_FILE" 2>&1 &

COLLECTOR_PID=$!

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
