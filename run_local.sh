#!/bin/bash
# Local Pipeline Runner
# Mimics the GitHub Actions workflow for local development and testing
# 
# Usage: ./run_local.sh [--full]
#   --full: Run full collection (default: test mode with 30 users)
#
# This script will automatically:
#   ✓ Install environment (conda or pip) if not found
#   ✓ Download PyPI official index (~708K packages from pypi.org)
#   ✓ Download Top PyPI rankings (15K packages from GitHub)
#   ✓ Collect GitHub data for Seattle developers
#   ✓ Generate frontend data and build
#   ✓ Start local development server

set -e  # Exit on error

# Cleanup function for Ctrl+C
cleanup() {
    echo ""
    log_warning "Interrupted! Cleaning up resources..."
    
    # Stop Celery workers
    if pgrep -f "celery.*worker" > /dev/null; then
        log_info "Stopping Celery workers..."
        pkill -f "celery.*worker" 2>/dev/null || true
        sleep 2
        log_success "Workers stopped"
    fi
    
    # Clean up temporary files
    if [ -f "data/removed_repos_log.json" ]; then
        rm -f data/removed_repos_log.json
        log_info "Cleaned up temporary log files"
    fi
    
    if [ -f "data/.collection_success" ]; then
        rm -f data/.collection_success
        log_info "Cleaned up success markers"
    fi
    
    log_success "Cleanup completed"
    exit 130
}

# Set trap for Ctrl+C (SIGINT) and other termination signals
trap cleanup SIGINT SIGTERM

# Parse arguments
FULL_MODE=false
if [[ "$1" == "--full" ]]; then
    FULL_MODE=true
fi

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Get script directory (run_local.sh is in project root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

cd "$PROJECT_ROOT"

# Check if conda environment exists
if command -v conda &> /dev/null; then
    # Check if ssr environment exists
    if ! conda env list | grep -q "^ssr "; then
        log_warning "ssr conda environment not found!"
        echo ""
        log_info "Please choose installation method:"
        echo "  1) conda env create -f environment.yml"
        echo "  2) pip install -e ."
        echo ""
        read -p "Install with conda (1) or pip (2)? (default: 1): " INSTALL_METHOD
        INSTALL_METHOD=${INSTALL_METHOD:-1}
        
        if [ "$INSTALL_METHOD" = "1" ]; then
            log_info "Creating conda environment from environment.yml..."
            conda env create -f environment.yml
            if [ $? -ne 0 ]; then
                log_error "Failed to create conda environment!"
                exit 1
            fi
            log_success "Conda environment created"
        elif [ "$INSTALL_METHOD" = "2" ]; then
            log_info "Installing with pip..."
            pip install -e .
            if [ $? -ne 0 ]; then
                log_error "Failed to install with pip!"
                exit 1
            fi
            log_success "Package installed with pip"
        else
            log_error "Invalid choice!"
            exit 1
        fi
    fi
    
    # Activate conda environment if using conda
    if conda env list | grep -q "^ssr "; then
        if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "ssr" ]; then
            log_info "Activating ssr conda environment..."
            eval "$(conda shell.bash hook)"
            conda activate ssr
            if [ $? -ne 0 ]; then
                log_error "Failed to activate ssr environment!"
                exit 1
            fi
            log_success "ssr environment activated"
        fi
    fi
else
    # No conda, check if package is installed
    log_info "Conda not found, checking pip installation..."
    if ! python3 -c "import seattle_source_ranker" 2>/dev/null; then
        log_warning "seattle_source_ranker not installed!"
        echo ""
        read -p "Install with pip? (y/n, default: y): " INSTALL_PIP
        INSTALL_PIP=${INSTALL_PIP:-y}
        
        if [[ "$INSTALL_PIP" == "y" || "$INSTALL_PIP" == "Y" ]]; then
            log_info "Installing with pip..."
            pip install -e .
            if [ $? -ne 0 ]; then
                log_error "Failed to install with pip!"
                exit 1
            fi
            log_success "Package installed with pip"
        else
            log_error "Package installation required to continue!"
            exit 1
        fi
    else
        log_success "seattle_source_ranker already installed"
    fi
fi

echo ""
echo "========================================="
if [ "$FULL_MODE" = true ]; then
    log_info "Seattle Source Ranker - FULL COLLECTION MODE"
else
    log_info "Seattle Source Ranker - TEST MODE (30 users)"
fi
echo "========================================="
log_info "Project root: $PROJECT_ROOT"
echo ""

# Environment Setup and Testing
log_step "1. Environment Setup & Token Testing"
echo "========================================="
echo ""

# Check if .env.tokens exists
log_info "Checking GitHub tokens..."
if [ ! -f ".env.tokens" ]; then
    log_error ".env.tokens not found!"
    log_info "Please create .env.tokens with your GitHub tokens:"
    echo "  GITHUB_TOKEN_1=ghp_xxxx"
    echo "  GITHUB_TOKEN_2=ghp_xxxx"
    echo "  ..."
    exit 1
fi

# Count tokens
TOKEN_COUNT=$(grep -c "^GITHUB_TOKEN_[0-9]=" .env.tokens || true)
log_success "Found $TOKEN_COUNT GitHub tokens in .env.tokens"

# Test tokens
log_info "Testing GitHub token validity..."
python3 << 'PYTHON_EOF'
from seattle_source_ranker.tokens import TokenManager
import sys

try:
    tm = TokenManager()
    tokens = tm.get_all_tokens()
    
    if not tokens:
        print("[ERROR] No valid tokens found!")
        sys.exit(1)
    
    print(f"[OK] {len(tokens)} tokens loaded and validated successfully")
        
except Exception as e:
    print(f"[ERROR] Token test failed: {e}")
    sys.exit(1)
PYTHON_EOF

if [ $? -ne 0 ]; then
    log_error "Token validation failed!"
    exit 1
fi

log_success "All tokens validated"
echo ""

# Check Python environment
log_info "Checking Python environment..."
python3 << 'PYTHON_EOF'
import sys
print(f"[OK] Python version: {sys.version.split()[0]}")

# Check required packages
required_packages = [
    'requests',
    'celery',
    'redis',
    'seattle_source_ranker'
]

missing = []
for pkg in required_packages:
    try:
        __import__(pkg.replace('-', '_'))
        print(f"[OK] {pkg} installed")
    except ImportError:
        print(f"[ERROR] {pkg} NOT installed")
        missing.append(pkg)

if missing:
    print(f"\n[ERROR] Missing packages: {', '.join(missing)}")
    print("Run: pip install -e .")
    sys.exit(1)
PYTHON_EOF

if [ $? -ne 0 ]; then
    log_error "Python environment check failed!"
    exit 1
fi

log_success "Python environment ready"
echo ""

# Check Redis
log_info "Checking Redis server..."
if ! pgrep -x redis-server > /dev/null; then
    log_warning "Redis server not running, starting it..."
    redis-server --daemonize yes
    sleep 2
    
    if pgrep -x redis-server > /dev/null; then
        log_success "Redis server started"
    else
        log_error "Failed to start Redis server"
        exit 1
    fi
else
    log_success "Redis server is already running"
fi

# Test Redis connection and clear any residual tasks
log_info "Checking for residual tasks in Redis..."
python3 << 'PYTHON_EOF'
import redis
import sys

try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("[OK] Redis connection successful")
    
    # Check for existing Celery tasks
    celery_keys = r.keys('celery*')
    if celery_keys:
        print(f"[WARN] Found {len(celery_keys)} residual Celery keys in Redis")
        print("[CLEAN] Clearing residual tasks...")
        for key in celery_keys:
            r.delete(key)
        print("[OK] All residual tasks cleared")
    else:
        print("[OK] No residual tasks found")
    
    # Also check for any other queue keys
    all_keys = r.keys('*')
    if all_keys:
        print(f"[INFO] Total Redis keys: {len(all_keys)}")
    else:
        print("[OK] Redis is clean (no keys)")
        
except Exception as e:
    print(f"[ERROR] Redis check failed: {e}")
    sys.exit(1)
PYTHON_EOF

if [ $? -ne 0 ]; then
    log_error "Redis cleanup failed!"
    exit 1
fi

# Stop any residual Celery workers
if pgrep -f "celery.*worker" > /dev/null; then
    log_warning "Found residual Celery workers, stopping them..."
    pkill -f "celery.*worker" 2>/dev/null || true
    sleep 2
    log_success "Residual workers stopped"
fi

log_success "Redis ready and clean"
echo ""
echo ""

# Data Collection
log_step "2. Data Collection"
echo "========================================="
echo ""

# Check user data age
log_info "Checking user data age..."
SKIP_GRAPHQL="false"

if [ -f "data/seattle_users.json" ]; then
    python3 << 'PYTHON_EOF'
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

SEATTLE_TZ = ZoneInfo("America/Los_Angeles")
user_file = Path('data/seattle_users.json')

try:
    with open(user_file, 'r') as f:
        data = json.load(f)
    
    collected_at = data.get('collected_at')
    if collected_at:
        file_time = datetime.fromisoformat(collected_at)
        now = datetime.now(SEATTLE_TZ)
        hours_since = (now - file_time).total_seconds() / 3600
        
        print(f"[FILE] User data collected: {file_time.isoformat()}")
        print(f"[TIME] Hours since: {hours_since:.1f}")
        
        if 0 <= hours_since < 24:
            print("[OK] User data is fresh (< 24 hours)")
            print("SKIP_GRAPHQL=true")
        else:
            print(f"[TIME] User data is old (>= 24 hours)")
            print("SKIP_GRAPHQL=false")
    else:
        print("[WARNING] No collected_at timestamp")
        print("SKIP_GRAPHQL=false")
except Exception as e:
    print(f"[ERROR] {e}")
    print("SKIP_GRAPHQL=false")
PYTHON_EOF
else
    log_warning "seattle_users.json not found, will run full collection"
fi

echo ""

# Ask user if they want to skip collection (with 3 second timeout)
if [ "$FULL_MODE" = true ]; then
    PROMPT="Run FULL collection (all users)? (y/n, default: y, auto in 3s): "
else
    PROMPT="Run TEST collection (30 users)? (y/n, default: y, auto in 3s): "
fi

# Use read with timeout
if read -t 3 -p "$PROMPT" RUN_COLLECTION; then
    echo ""  # New line after input
else
    echo ""  # New line after timeout
    log_info "No input received, continuing with default (yes)..."
    RUN_COLLECTION="y"
fi

RUN_COLLECTION=${RUN_COLLECTION:-y}

if [[ "$RUN_COLLECTION" == "y" || "$RUN_COLLECTION" == "Y" ]]; then
    if [ "$FULL_MODE" = true ]; then
        log_info "Starting FULL distributed collection..."
    else
        log_info "Starting TEST distributed collection (30 users)..."
    fi
    
    # Check if Redis is running
    if ! pgrep -x redis-server > /dev/null; then
        log_warning "Redis server not running, starting it..."
        redis-server --daemonize yes
        sleep 2
    fi
    log_success "Redis server is running"
    
    # Start Celery workers
    log_info "Starting Celery workers..."
    bash scripts/start_workers.sh
    sleep 3
    
    # Run collection
    log_info "Running distributed collection..."
    
    if [ "$FULL_MODE" = true ]; then
        FULL_MODE_PY="True"
        OUTPUT_FILE="data/seattle_projects.json"
    else
        FULL_MODE_PY="False"
        OUTPUT_FILE="data/seattle_projects.json"
    fi
    
    python3 << PYTHON_EOF
from seattle_source_ranker.collector.distributed_collector import DistributedCollector
import sys

try:
    collector = DistributedCollector()
    
    # Determine user limit and output file based on mode
    if ${FULL_MODE_PY}:
        # Full mode: collect all Seattle users (~30K)
        user_limit = None
        max_users = 50000  # High limit to ensure we get everyone
        print("[INFO] Full mode: collecting all Seattle users (~30K)")
    else:
        # Test mode: only 30 users
        user_limit = 30
        max_users = 30
        print(f"[INFO] Test mode: collecting {user_limit} users")
    
    output_file = "${OUTPUT_FILE}"
    print(f"[INFO] Output file: {output_file}")
    
    # Call collect with explicit max_users
    if user_limit:
        collector.collect(user_limit=user_limit, output_file=output_file)
    else:
        collector.collect(max_users=max_users, output_file=output_file)
    
    print("[OK] Collection completed successfully")
    print(f"[OK] Data saved to: {output_file}")
except Exception as e:
    print(f"[ERROR] Collection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_EOF
    
    # Stop workers
    log_info "Stopping Celery workers..."
    bash scripts/stop_workers.sh
    
    log_success "Data collection completed"
    echo ""
else
    log_info "Skipping data collection, using existing data"
    echo ""
fi

# Update PyPI official package index
log_info "Updating PyPI official package index..."
python3 scripts/update_pypi_official_index.py
log_success "PyPI official index updated"
echo ""

# Generate PyPI projects list
log_info "Generating PyPI projects list..."
# Use the standard output file from collection
if [ -f "data/seattle_projects.json" ]; then
    LATEST_PROJECTS="data/seattle_projects.json"
elif [ -f "data/seattle_projects_latest.json" ]; then
    LATEST_PROJECTS="data/seattle_projects_latest.json"
else
    # Try to find timestamped file
    LATEST_PROJECTS=$(ls -t data/seattle_projects_*.json 2>/dev/null | head -n 1)
fi

if [ -z "$LATEST_PROJECTS" ]; then
    log_error "No seattle_projects file found!"
    log_info "Expected files: data/seattle_projects.json or data/seattle_projects_*.json"
    exit 1
fi
log_info "Processing: $LATEST_PROJECTS"
python3 scripts/generate_pypi_projects.py "$LATEST_PROJECTS"
log_success "PyPI projects list generated"
echo ""

# Update Top PyPI packages ranking
log_info "Checking for Top PyPI packages updates..."
python3 scripts/update_top_pypi_packages.py

# Check if top_pypi_packages.json was modified
if git diff --quiet data/top_pypi_packages.json 2>/dev/null; then
    log_info "Top PyPI already up to date"
else
    log_success "Top PyPI updated to new version"
    log_info "Extracting Top PyPI matches..."
    python3 scripts/extract_top_pypi_matches.py
    python3 scripts/verify_pypi_owners.py
    log_success "Top PyPI matches extracted and verified"
fi
echo ""

# Validate and enrich data (secondary update)
log_info "Running secondary validation and enrichment..."
# Use the standard output file from collection
if [ -f "data/seattle_projects.json" ]; then
    LATEST_PROJECTS="data/seattle_projects.json"
elif [ -f "data/seattle_projects_latest.json" ]; then
    LATEST_PROJECTS="data/seattle_projects_latest.json"
else
    # Try to find timestamped file
    LATEST_PROJECTS=$(ls -t data/seattle_projects_*.json 2>/dev/null | head -n 1)
fi

if [ -z "$LATEST_PROJECTS" ]; then
    log_error "No seattle_projects file found for validation!"
    exit 1
fi
log_info "Processing: $LATEST_PROJECTS"

# Start Celery workers for validation
if ! pgrep -x redis-server > /dev/null; then
    redis-server --daemonize yes
    sleep 2
fi
bash scripts/start_workers.sh
sleep 3

python3 scripts/secondary_update.py "$LATEST_PROJECTS"

# Stop workers
bash scripts/stop_workers.sh

# Clean up temporary log file
if [ -f "data/removed_repos_log.json" ]; then
    rm data/removed_repos_log.json
    log_info "Cleaned up temporary log files"
fi

log_success "Data validated and enriched → data/seattle_projects.json"
echo ""

# Generate frontend paginated data
log_info "Generating frontend data with topics..."
python3 scripts/generate_frontend_data.py
log_success "Frontend data generated"
echo ""

# Build frontend
log_info "Building frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    log_info "Installing frontend dependencies..."
    npm install
fi

log_info "Running npm build..."
npm run build

cd "$PROJECT_ROOT"
log_success "Frontend built successfully"
echo ""

# Summary
log_success "========================================="
if [ "$FULL_MODE" = true ]; then
    log_success "FULL Pipeline completed successfully!"
else
    log_success "TEST Pipeline completed successfully!"
fi
log_success "========================================="
echo ""
if [ "$FULL_MODE" = true ]; then
    log_info "Full collection mode completed"
    log_info "All Seattle users processed"
else
    log_info "Test collection mode completed"
    log_info "30 users processed for testing"
    log_warning "Use --full flag for complete production collection"
fi
echo ""
log_info "Frontend build located at: frontend/build/"
echo ""

# Ask if user wants to start local server (with 3 second timeout)
PROMPT="Start local development server? (y/n, default: y, auto in 3s): "

if read -t 3 -p "$PROMPT" START_SERVER; then
    echo ""  # New line after input
else
    echo ""  # New line after timeout
    log_info "No input received, starting server..."
    START_SERVER="y"
fi

START_SERVER=${START_SERVER:-y}

if [[ "$START_SERVER" == "y" || "$START_SERVER" == "Y" ]]; then
    log_info "Starting local development server..."
    log_info "Server will open in your browser at http://localhost:3000"
    log_info "Press Ctrl+C to stop the server"
    echo ""
    
    cd frontend
    npm start
else
    log_info "To start the server later, run:"
    echo "  cd frontend && npm start"
fi
