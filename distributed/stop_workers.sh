#!/bin/bash
# Script to stop all Celery workers

echo "🛑 Stopping all Celery workers..."

# Find and kill all celery worker processes
pkill -f 'celery.*collection_worker'

if [ $? -eq 0 ]; then
    echo "✅ All workers stopped"
else
    echo "⚠️  No workers found running"
fi

# Clean up any stale files
rm -f celerybeat-schedule.db
rm -f celerybeat.pid

echo "Done!"
