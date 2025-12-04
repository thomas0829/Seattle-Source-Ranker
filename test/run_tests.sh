#!/bin/bash
# Run tests without ROS interference

cd "$(dirname "$0")"

echo "[TEST] Running Seattle Source Ranker Tests..."
echo ""

# Set PYTHONPATH to project root
export PYTHONPATH="$(dirname "$PWD")"

# Run pytest from test directory with minimal plugins
python3 -m pytest . -v --override-ini="plugins=" --tb=short "$@"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "[OK] All tests passed!"
else
    echo ""
    echo "[ERROR] Some tests failed (exit code: $exit_code)"
fi

exit $exit_code
