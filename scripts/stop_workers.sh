#!/bin/bash
# Script to stop all Celery workers

echo "🛑 Stopping all Celery workers..."

# First try graceful shutdown (SIGTERM)
pkill -15 -f 'celery.*collection_worker'

# Wait up to 10 seconds for graceful shutdown
for i in {1..10}; do
    if ! pgrep -f 'celery.*collection_worker' > /dev/null; then
        echo "[OK] All workers stopped gracefully"
        break
    fi
    sleep 1
done

# If still running, force kill (SIGKILL)
if pgrep -f 'celery.*collection_worker' > /dev/null; then
    echo "[WARNING] Workers still running, forcing shutdown..."
    pkill -9 -f 'celery.*collection_worker'
    sleep 2
    
    if pgrep -f 'celery.*collection_worker' > /dev/null; then
        echo "[ERROR] Some workers could not be stopped!"
    else
        echo "[OK] Workers force-stopped"
    fi
fi

# Clean up any stale files
rm -f celerybeat-schedule.db
rm -f celerybeat.pid

echo "Done!"
