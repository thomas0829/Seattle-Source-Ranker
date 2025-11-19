"""
Distributed Collection Coordinator

Coordinates multiple Celery workers to collect Seattle projects in parallel.
Uses Redis as message broker and PostgreSQL for data persistence.

Usage:
    python3 distributed_collector.py --max-users 50000 --workers 8 --batch-size 50
"""
import argparse
import os
import sys
import json
import time
import subprocess
import signal
import atexit
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Any
from celery import group

# 西雅圖時區
SEATTLE_TZ = ZoneInfo("America/Los_Angeles")
from celery.result import GroupResult

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from distributed.workers.collection_worker import (
    search_seattle_users_task,
    fetch_users_batch_task,
    collect_seattle_projects_task
)
from utils.celery_config import celery_app


class DistributedCollector:
    """
    Coordinator for distributed data collection
    
    Responsibilities:
    - Search for Seattle developers (REST API or GraphQL)
    - Split developers into batches
    - Distribute batches to workers
    - Monitor progress
    - Aggregate and save results
    """
    
    # Pre-optimized filters shared by both REST and GraphQL search
    # Strategy: repos>=10 all users, repos:1-9 only followers>=5 (quality filter)
    # Total: ~28,000 users (24K high-activity + 4K quality low-repo)
    PREOPTIMIZED_FILTERS = [
        # High activity users - repos>=10 (all users, no follower restriction)
        "repos:>=500",
        "repos:300..499",
        "repos:200..299",
        "repos:150..199",
        "repos:100..149",
        "repos:80..99",
        "repos:60..69",
        "repos:70..79",
        "repos:50..54",
        "repos:55..59",
        "repos:40..42",
        "repos:43..44",
        "repos:45..49",
        "repos:30..31",
        "repos:32",
        "repos:33..34",
        "repos:35..37",
        "repos:38..39",
        "repos:20",
        "repos:21",
        "repos:22",
        "repos:23",
        "repos:24",
        "repos:25",
        "repos:26",
        "repos:27",
        "repos:28..29",
        "repos:15",
        "repos:16",
        "repos:17",
        "repos:18",
        "repos:19",
        # repos:10-14 need followers subdivision (all users)
        "repos:10 followers:>=100",
        "repos:10 followers:50..99",
        "repos:10 followers:20..49",
        "repos:10 followers:10..19",
        "repos:10 followers:5..9",
        "repos:10 followers:1..4",
        "repos:10 followers:0",
        "repos:11 followers:>=100",
        "repos:11 followers:50..99",
        "repos:11 followers:20..49",
        "repos:11 followers:10..19",
        "repos:11 followers:5..9",
        "repos:11 followers:1..4",
        "repos:11 followers:0",
        "repos:12 followers:>=100",
        "repos:12 followers:50..99",
        "repos:12 followers:20..49",
        "repos:12 followers:10..19",
        "repos:12 followers:5..9",
        "repos:12 followers:1..4",
        "repos:12 followers:0",
        "repos:13 followers:>=100",
        "repos:13 followers:50..99",
        "repos:13 followers:20..49",
        "repos:13 followers:10..19",
        "repos:13 followers:5..9",
        "repos:13 followers:1..4",
        "repos:13 followers:0",
        "repos:14 followers:>=100",
        "repos:14 followers:50..99",
        "repos:14 followers:20..49",
        "repos:14 followers:10..19",
        "repos:14 followers:5..9",
        "repos:14 followers:1..4",
        "repos:14 followers:0",
        # Low repo count - only quality users (followers>=5)
        # repos:1-9 with followers>=5: ~4K users, all ranges < 500
        "repos:1 followers:>=5",
        "repos:2 followers:>=5",
        "repos:3 followers:>=5",
        "repos:4 followers:>=5",
        "repos:5 followers:>=5",
        "repos:6 followers:>=5",
        "repos:7 followers:>=5",
        "repos:8 followers:>=5",
        "repos:9 followers:>=5",
    ]
    
    def __init__(self, batch_size: int = 10, auto_manage_workers: bool = True, num_workers: int = 8, concurrency: int = 2):
        """
        Args:
            batch_size: Number of users per worker batch
            auto_manage_workers: Automatically start/stop workers
            num_workers: Number of workers to start if auto_manage_workers is True
            concurrency: Number of concurrent tasks per worker
        """
        self.batch_size = batch_size
        self.results = []
        self.auto_manage_workers = auto_manage_workers
        self.num_workers = num_workers
        self.concurrency = concurrency
        self.worker_processes = []
        
        # Register cleanup on exit
        if auto_manage_workers:
            atexit.register(self.cleanup_workers)
    
    def check_workers(self) -> int:
        """
        Check how many workers are currently running
        
        Returns:
            Number of active workers
        """
        try:
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            return len(stats) if stats else 0
        except Exception:
            return 0
    
    def start_workers(self):
        """
        Automatically start Celery workers if none are running
        """
        active_workers = self.check_workers()
        
        if active_workers >= self.num_workers:
            print(f"✅ Found {active_workers} active workers (target: {self.num_workers})")
            return
        
        print(f"🚀 Starting {self.num_workers} Celery workers...")
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Create logs directory with date subdirectory
        date_str = datetime.now(SEATTLE_TZ).strftime("%Y%m%d")
        log_dir = os.path.join(project_root, "logs", date_str)
        os.makedirs(log_dir, exist_ok=True)
        
        # Timestamp for this run (time only, no date in filename)
        timestamp = datetime.now(SEATTLE_TZ).strftime("%H%M%S")
        
        for i in range(1, self.num_workers + 1):
            log_file = os.path.join(log_dir, f"worker_{i}_{timestamp}.log")
            
            # Start worker process
            cmd = [
                sys.executable, "-m", "celery",
                "-A", "distributed.workers.collection_worker",
                "worker",
                "--loglevel=info",
                f"--concurrency={self.concurrency}",
                f"-n", f"worker{i}@%h"
            ]
            
            with open(log_file, "w") as log:
                process = subprocess.Popen(
                    cmd,
                    cwd=project_root,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid  # Create new process group
                )
                self.worker_processes.append(process)
            
            print(f"   Worker {i} started (PID: {process.pid}, log: {log_file})")
        
        # Wait for workers to register
        print("   Waiting for workers to register...", end="", flush=True)
        max_wait_iterations = 60  # Wait up to 30 seconds
        for i in range(max_wait_iterations):
            time.sleep(0.5)
            active = self.check_workers()
            if active >= self.num_workers:
                print(f" ✅ {active} workers ready!")
                return
            if i % 10 == 0 and i > 0:  # Every 5 seconds
                print(f"\n   ({active}/{self.num_workers} workers registered, waiting...)", end="", flush=True)
            print(".", end="", flush=True)
        
        final_count = self.check_workers()
        if final_count > 0:
            print(f"\n   ⚠️  Only {final_count} workers registered (expected {self.num_workers})")
            print(f"   Continuing with {final_count} workers...")
        else:
            print(f"\n   ❌ No workers registered after 30 seconds!")
            raise RuntimeError("Failed to start workers")
    
    def cleanup_workers(self):
        """
        Stop all started workers on exit
        """
        if not self.worker_processes:
            return
        
        print(f"\n🛑 Stopping {len(self.worker_processes)} workers...")
        
        for process in self.worker_processes:
            try:
                # Send SIGTERM to process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
                print(f"   Worker {process.pid} stopped")
            except Exception as e:
                # Force kill if SIGTERM doesn't work
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    print(f"   Worker {process.pid} force killed")
                except Exception:
                    pass
        
        self.worker_processes = []
        print("✅ All workers stopped")
    
    def find_recent_user_file(self, min_users: int = 20000) -> str:
        """
        Find the most recent user file with at least min_users
        
        Args:
            min_users: Minimum number of users required
            
        Returns:
            Path to user file, or None if not found
        """
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        
        if not os.path.exists(data_dir):
            return None
        
        # Find all seattle_users_*.json files
        user_files = []
        for filename in os.listdir(data_dir):
            if filename.startswith("seattle_users_") and filename.endswith(".json"):
                filepath = os.path.join(data_dir, filename)
                try:
                    # Check file size and modification time
                    stat = os.stat(filepath)
                    mtime = stat.st_mtime
                    
                    # Quick check: if file is large enough, it probably has enough users
                    # 28K users ~= 480KB
                    if stat.st_size < 400000:  # Less than 400KB, probably too small
                        continue
                    
                    user_files.append((filepath, mtime))
                except Exception:
                    continue
        
        if not user_files:
            return None
        
        # Sort by modification time (newest first)
        user_files.sort(key=lambda x: x[1], reverse=True)
        
        # Check the most recent file
        for filepath, _ in user_files:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        user_count = len(data)
                    elif isinstance(data, dict) and 'usernames' in data:
                        user_count = len(data['usernames'])
                    else:
                        continue
                    
                    if user_count >= min_users:
                        return filepath, user_count
            except Exception:
                continue
        
        return None
    
    def load_or_search_users(self, max_users: int, start_user: int = 0) -> List[str]:
        """
        Load users from existing file if available (>20K users, <3 days old),
        otherwise search for new users
        
        Args:
            max_users: Maximum number of users to find
            start_user: Starting index for segmented collection
            
        Returns:
            List of GitHub usernames
        """
        # Try to find recent user file
        result = self.find_recent_user_file(min_users=20000)
        
        if result:
            filepath, user_count = result
            filename = os.path.basename(filepath)
            
            # Parse timestamp from filename (format: seattle_users_YYYYMMDD_HHMMSS.json)
            # This is more reliable than file mtime in CI environments
            try:
                timestamp_str = filename.replace('seattle_users_', '').replace('.json', '')
                date_part, time_part = timestamp_str.split('_')
                
                # Parse date and time
                year = int(date_part[0:4])
                month = int(date_part[4:6])
                day = int(date_part[6:8])
                hour = int(time_part[0:2])
                minute = int(time_part[2:4])
                second = int(time_part[4:6])
                
                # Create datetime with Seattle timezone
                file_time = datetime(year, month, day, hour, minute, second, tzinfo=SEATTLE_TZ)
                now = datetime.now(SEATTLE_TZ)
                age_hours = (now - file_time).total_seconds() / 3600
            except Exception as e:
                print(f"   ⚠️  Failed to parse timestamp from filename: {e}")
                print(f"   Falling back to user search...")
                return self.search_users(max_users, start_user)
            
            if age_hours < 24:  # Less than 1 day
                print(f"🔍 Step 1: Loading existing user data...")
                print(f"   File: {filename}")
                print(f"   Users: {user_count:,}")
                print(f"   Age: {age_hours:.1f} hours")
                print(f"   ✅ Using cached user list (skip user search)")
                
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            usernames = data[start_user:start_user + max_users]
                        elif isinstance(data, dict) and 'usernames' in data:
                            usernames = data['usernames'][start_user:start_user + max_users]
                        else:
                            raise ValueError("Invalid user file format")
                    
                    print(f"   Loaded: {len(usernames):,} users (from index {start_user})")
                    return usernames
                    
                except Exception as e:
                    print(f"   ⚠️  Failed to load file: {e}")
                    print(f"   Falling back to user search...")
            else:
                print(f"🔍 Step 1: Found user file but it's too old ({age_hours:.1f} hours)")
                print(f"   Performing fresh user search...")
        else:
            print(f"🔍 Step 1: No recent user file found (need >20K users)")
            print(f"   Performing user search...")
        
        # Fall back to search
        return self.search_users(max_users, start_user)
    
    def search_users(self, max_users: int, start_user: int = 0) -> List[str]:
        """
        Search for Seattle developers using GraphQL API (5000 req/hour vs REST Search 30 req/min)
        
        Args:
            max_users: Maximum number of users to find
            start_user: Starting index for segmented collection
            
        Returns:
            List of GitHub usernames
        """
        import requests
        
        print(f"🔍 Step 1: Searching for Seattle developers (GraphQL)...")
        print(f"   Target: {max_users} users (starting from index {start_user})")
        print(f"   Strategy: GraphQL Search API (5000 req/hour limit)")
        
        # Use TokenManager for multi-token support
        from utils.token_manager import get_token_manager
        try:
            tm = get_token_manager()
            print(f"   Using multi-token rotation ({tm.get_token_count()} tokens)")
            use_token_manager = True
        except Exception as e:
            print(f"   ⚠️  TokenManager not available: {e}")
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                raise ValueError("GITHUB_TOKEN environment variable not set")
            print(f"   Using single token")
            use_token_manager = False
        
        usernames_set = set()
        
        # GraphQL search query
        query_template = """
        query($searchQuery: String!, $cursor: String) {
          search(query: $searchQuery, type: USER, first: 100, after: $cursor) {
            userCount
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              ... on User {
                login
              }
            }
          }
        }
        """
        
        # Use shared pre-optimized filters (same as REST API)
        repo_filters = self.PREOPTIMIZED_FILTERS
        
        print(f"   Using {len(repo_filters)} pre-optimized filters")
        print(f"   (Same strategy as REST API for ~28K users)")
        
        for idx, repo_filter in enumerate(repo_filters, 1):
            if len(usernames_set) >= max_users:
                break
                
            search_query = f"location:seattle {repo_filter}"
            print(f"   [{idx}/{len(repo_filters)}] Searching: {search_query}")
            
            cursor = None
            page = 1
            filter_users = 0
            
            while len(usernames_set) < max_users:
                # Get fresh token with smart selection
                if use_token_manager:
                    current_token = tm.get_token()
                else:
                    current_token = token
                
                headers = {
                    "Authorization": f"bearer {current_token}",
                    "Content-Type": "application/json",
                }
                
                variables = {
                    "searchQuery": search_query,
                    "cursor": cursor
                }
                
                response = requests.post(
                    'https://api.github.com/graphql',
                    json={'query': query_template, 'variables': variables},
                    headers=headers,
                    timeout=10
                )
                
                # Check rate limit from response headers
                remaining = int(response.headers.get('X-RateLimit-Remaining', 999))
                
                # Proactive rate limit handling - check before hitting limit
                if remaining < 100:
                    if use_token_manager:
                        # Check all tokens to find the best one
                        best_token = None
                        best_remaining = 0
                        min_reset_time = float('inf')
                        token_status = []
                        
                        for i in range(tm.get_token_count()):
                            check_token = tm._tokens[i]
                            check_headers = {'Authorization': f'bearer {check_token}'}
                            check_query = '{ rateLimit { remaining limit resetAt } }'
                            
                            try:
                                check_response = requests.post(
                                    'https://api.github.com/graphql',
                                    json={'query': check_query},
                                    headers=check_headers,
                                    timeout=5
                                )
                                if check_response.status_code == 200:
                                    data = check_response.json()
                                    if 'data' in data and 'rateLimit' in data['data']:
                                        rate_limit = data['data']['rateLimit']
                                        token_remaining = rate_limit['remaining']
                                        token_status.append(f"Token{i+1}:{token_remaining}/{rate_limit['limit']}")
                                        
                                        # Find token with most remaining quota
                                        if token_remaining > best_remaining:
                                            best_remaining = token_remaining
                                            best_token = check_token
                                        
                                        # Track reset time if needed
                                        if token_remaining < 100:
                                            from dateutil import parser
                                            reset_at = parser.parse(rate_limit['resetAt'])
                                            reset_timestamp = reset_at.timestamp()
                                            if reset_timestamp < min_reset_time:
                                                min_reset_time = reset_timestamp
                            except Exception as e:
                                print(f"      ⚠️ Failed to check token {i+1}: {e}")
                        
                        if best_remaining > 100:
                            # Found a token with good quota
                            print(f"      ✅ Switched to better token ({', '.join(token_status)})")
                            current_token = best_token
                            headers["Authorization"] = f"bearer {current_token}"
                            # Force update TokenManager to use this token next
                            tm._current_index = tm._tokens.index(best_token)
                        elif min_reset_time != float('inf'):
                            # All tokens exhausted, wait for earliest recovery
                            wait_time = max(min_reset_time - time.time(), 0) + 60
                            print(f"      ⏳ All tokens low, waiting {wait_time:.0f}s for earliest recovery...")
                            print(f"         Status: {', '.join(token_status)}")
                            time.sleep(wait_time)
                            current_token = tm.get_token(force_check=True)
                            headers["Authorization"] = f"bearer {current_token}"
                        else:
                            # Fallback: wait 60s
                            print(f"      ⏳ Rate limit low ({remaining}), waiting 60s...")
                            time.sleep(60)
                    else:
                        # Single token mode - just wait
                        reset_at = response.headers.get('X-RateLimit-Reset')
                        if reset_at:
                            wait_time = max(int(reset_at) - time.time(), 0) + 60
                        else:
                            wait_time = 60
                        print(f"      ⏳ Rate limit low ({remaining}), waiting {wait_time:.0f}s...")
                        time.sleep(wait_time)
                    continue
                
                if response.status_code != 200:
                    if response.status_code == 403:
                        # Secondary rate limit or token issue
                        if use_token_manager:
                            # Try to find another token
                            print(f"      ⚠️ 403 error, checking other tokens...")
                            current_token = tm.get_token(force_check=True)
                            headers["Authorization"] = f"bearer {current_token}"
                            time.sleep(10)  # Brief wait
                            continue
                        else:
                            wait_time = 60
                            print(f"      ⚠️ Rate limit (403) - waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                    else:
                        print(f"      ⚠️ API returned status {response.status_code}, moving to next filter")
                        break
                
                data = response.json()
                
                if 'errors' in data:
                    print(f"      ⚠️ GraphQL errors: {data['errors'][0]['message']}")
                    break
                
                search_result = data.get('data', {}).get('search', {})
                users = search_result.get('nodes', [])
                page_info = search_result.get('pageInfo', {})
                
                if not users:
                    break
                
                for user in users:
                    if user and 'login' in user:
                        usernames_set.add(user['login'])
                        filter_users += 1
                
                print(f"      Page {page}: +{len(users)} users (filter: {filter_users}, total: {len(usernames_set)})", end="\r", flush=True)
                
                # Check if there are more pages
                if not page_info.get('hasNextPage') or len(usernames_set) >= max_users:
                    print()  # New line
                    break
                
                cursor = page_info.get('endCursor')
                page += 1
                time.sleep(1.0)  # Rate limit prevention
            
            print()  # New line after filter complete
            time.sleep(2.0)  # Wait between filters
        
        # Convert set to list and truncate
        usernames = list(usernames_set)[:max_users]
        
        print(f"✅ Found {len(usernames)} unique developers (requested: {max_users})")
        
        # Save to file
        timestamp = datetime.now(SEATTLE_TZ).strftime("%Y%m%d_%H%M%S")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        usernames_file = os.path.join(project_root, "data", f"seattle_users_{timestamp}.json")
        os.makedirs(os.path.dirname(usernames_file), exist_ok=True)
        
        with open(usernames_file, "w", encoding="utf-8") as f:
            json.dump({
                "total_users": len(usernames),
                "collected_at": datetime.now(SEATTLE_TZ).isoformat(),
                "query_strategy": "graphql multi-filter",
                "filters_used": len(repo_filters),
                "usernames": usernames
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved usernames to: {usernames_file}")
        
        return usernames
    
    def create_batches(self, usernames: List[str]) -> List[List[str]]:
        """
        Split users into batches for parallel processing
        
        Args:
            usernames: List of GitHub usernames
            
        Returns:
            List of username batches
        """
        batches = [
            usernames[i:i + self.batch_size]
            for i in range(0, len(usernames), self.batch_size)
        ]
        
        print(f"\n📦 Step 2: Created {len(batches)} batches")
        print(f"   Batch size: {self.batch_size} users/batch")
        print(f"   Total users: {len(usernames)}")
        
        return batches
    
    def distribute_tasks(self, batches: List[List[str]]) -> GroupResult:
        """
        Distribute batches to workers using Celery group
        
        Args:
            batches: List of username batches
            
        Returns:
            Celery GroupResult for monitoring
        """
        print(f"\n⚡ Step 3: Distributing tasks to workers...")
        print(f"   Spawning {len(batches)} parallel tasks")
        
        # Create parallel tasks
        job = group(fetch_users_batch_task.s(batch) for batch in batches)
        result = job.apply_async()
        
        print(f"✅ Tasks submitted to queue")
        return result
    
    def monitor_progress(self, result: GroupResult, total_batches: int):
        """
        Monitor and display progress of distributed tasks
        
        Args:
            result: Celery GroupResult
            total_batches: Total number of batches
        """
        print(f"\n📊 Step 4: Monitoring progress...")
        print(f"   Total batches: {total_batches}")
        print(f"   Waiting for workers...\n")
        
        start_time = time.time()
        last_completed = 0
        shown_errors = set()
        last_progress_time = time.time()
        
        # Add timeout to prevent hanging - only timeout when no progress
        max_idle_time = 7200  # 2 hours without any progress
        max_total_time = 18000  # 5 hours total (considering rate limit waiting time)
        
        while not result.ready():
            completed = result.completed_count()
            elapsed = time.time() - start_time
            idle_time = time.time() - last_progress_time
            
            # Update progress time
            if completed != last_completed:
                last_progress_time = time.time()
            
            # Timeout check - only timeout when no real progress
            if idle_time > max_idle_time:
                print(f"\n⚠️  No progress for {idle_time:.0f}s (max idle: {max_idle_time}s)", flush=True)
                print(f"   Completed so far: {completed}/{total_batches}", flush=True)
                print(f"   Tasks may have stalled, stopping...", flush=True)
                break
            
            if elapsed > max_total_time:
                print(f"\n⚠️  Total timeout after {elapsed:.1f}s", flush=True)
                print(f"   Completed so far: {completed}/{total_batches}", flush=True)
                break
            
            # If all tasks completed, force exit
            if completed >= total_batches:
                print(f"\n✅ All {total_batches} tasks completed!", flush=True)
                break
            
            # Check for failures
            failed_count = 0
            for task_result in result.results:
                if task_result.failed():
                    failed_count += 1
                    task_id = task_result.id
                    if task_id not in shown_errors:
                        try:
                            error = task_result.result
                            print(f"   ❌ Task {task_id[:8]} failed: {error}", flush=True)
                        except Exception as e:
                            print(f"   ❌ Task {task_id[:8]} failed: {str(e)}", flush=True)
                        shown_errors.add(task_id)
            
            if completed != last_completed or failed_count > 0:
                progress = (completed / total_batches) * 100
                
                status = f"   Progress: {completed}/{total_batches} batches ({progress:.1f}%)"
                if failed_count > 0:
                    status += f" | Failed: {failed_count}"
                status += f" | Elapsed: {elapsed:.1f}s"
                
                print(status, flush=True)
                last_completed = completed
            
            time.sleep(2)
        
        elapsed = time.time() - start_time
        print(f"\n✅ All tasks completed in {elapsed:.1f}s", flush=True)
    
    def retry_failed_tasks(self, result: GroupResult, original_batches: List[List[str]]) -> GroupResult:
        """
        Retry failed tasks
        
        Args:
            result: Original GroupResult
            original_batches: Original batch list to identify failed batches
            
        Returns:
            New GroupResult with retry tasks, or original if no failures
        """
        failed_tasks = []
        failed_batch_indices = []
        
        # Collect failed tasks
        for idx, task_result in enumerate(result.results):
            if task_result.failed():
                failed_tasks.append(task_result)
                failed_batch_indices.append(idx)
        
        if not failed_tasks:
            print(f"✅ No failed tasks to retry")
            return result
        
        print(f"\n🔄 Retrying {len(failed_tasks)} failed tasks...")
        
        # Create retry batches
        retry_batches = [original_batches[idx] for idx in failed_batch_indices]
        
        # Submit retry tasks
        retry_jobs = group([
            fetch_users_batch_task.s(batch)
            for batch in retry_batches
        ])
        
        retry_result = retry_jobs.apply_async()
        
        print(f"   Submitted {len(retry_batches)} retry tasks")
        print(f"   Monitoring retry progress...")
        
        # Monitor retry progress
        start_time = time.time()
        last_completed = 0
        shown_errors = set()
        
        while True:
            completed = retry_result.completed_count()
            elapsed = time.time() - start_time
            
            if completed >= len(retry_batches):
                print(f"\n✅ All retry tasks completed!")
                break
            
            if elapsed > 3600:  # 1 hour timeout for retries
                print(f"\n⚠️  Retry timeout after {elapsed:.1f}s")
                break
            
            # Check for failures
            failed_count = 0
            for task_result in retry_result.results:
                if task_result.failed():
                    failed_count += 1
                    task_id = task_result.id
                    if task_id not in shown_errors:
                        try:
                            error = task_result.result
                            print(f"   ❌ Retry task {task_id[:8]} failed: {error}", flush=True)
                        except Exception:
                            pass
                        shown_errors.add(task_id)
            
            if completed != last_completed:
                progress = (completed / len(retry_batches)) * 100
                status = f"   Retry: {completed}/{len(retry_batches)} ({progress:.1f}%)"
                if failed_count > 0:
                    status += f" | Still failed: {failed_count}"
                status += f" | Elapsed: {elapsed:.1f}s"
                print(status, flush=True)
                last_completed = completed
            
            time.sleep(2)
        
        # Merge retry results with original results
        print(f"\n📦 Merging retry results with original...")
        
        # Replace failed results with retry results
        for i, retry_idx in enumerate(failed_batch_indices):
            if i < len(retry_result.results):
                result.results[retry_idx] = retry_result.results[i]
        
        return result
    
    def aggregate_results(self, result: GroupResult, checkpoint_file: str = None) -> Dict[str, Any]:
        """
        Aggregate results from all workers with checkpoint saving
        
        Args:
            result: Celery GroupResult
            checkpoint_file: Optional checkpoint file path for incremental saves
            
        Returns:
            Aggregated results
        """
        print(f"\n📥 Step 5: Aggregating results...")
        
        batch_results = result.get(timeout=3600)  # 60 minutes timeout (increased for large collections)
        
        all_projects = []
        total_users_checked = 0
        total_users_successful = 0
        total_users_failed = 0
        total_users_filtered = 0
        
        # Aggregate failure reasons
        aggregated_failures = {
            "user_not_found": 0,
            "rate_limit": 0,
            "api_error": 0,
            "exception": 0,
            "filtered_criteria": 0
        }
        
        for batch_result in batch_results:
            all_projects.extend(batch_result["repos"])
            total_users_checked += batch_result.get("checked_users", batch_result.get("batch_size", 0))
            total_users_successful += batch_result["successful_users"]
            total_users_failed += batch_result["failed_users"]
            total_users_filtered += batch_result.get("filtered_users", 0)
            
            # Aggregate failure reasons if available
            if "failure_reasons" in batch_result:
                for reason, count in batch_result["failure_reasons"].items():
                    aggregated_failures[reason] += count
        
        print(f"   Raw projects collected: {len(all_projects)}")
        print(f"   Users checked: {total_users_checked}")
        print(f"   Successful users: {total_users_successful}")
        print(f"   Filtered users: {total_users_filtered}")
        print(f"   Failed users: {total_users_failed}")
        
        if total_users_filtered > 0:
            print(f"\n   📊 Filtered Analysis:")
            print(f"      Doesn't meet criteria (repos/followers): {aggregated_failures.get('filtered_criteria', 0)}")
        
        if total_users_failed > 0:
            print(f"\n   📊 Failure Analysis:")
            print(f"      User not found/inaccessible: {aggregated_failures['user_not_found']} ({aggregated_failures['user_not_found']/total_users_failed*100:.1f}%)")
            print(f"      Rate limit hits: {aggregated_failures['rate_limit']} ({aggregated_failures['rate_limit']/total_users_failed*100:.1f}%)")
            print(f"      API errors: {aggregated_failures['api_error']} ({aggregated_failures['api_error']/total_users_failed*100:.1f}%)")
            print(f"      Exceptions: {aggregated_failures['exception']} ({aggregated_failures['exception']/total_users_failed*100:.1f}%)")
        
        # Sort by stars
        all_projects.sort(key=lambda x: x["stars"], reverse=True)
        
        total_stars = sum(p["stars"] for p in all_projects)
        
        print(f"\n   Total {len(all_projects)} projects collected")
        print(f"   Total stars: {total_stars:,}")
        
        if all_projects:
            top_project = all_projects[0]
            print(f"   #1 project: {top_project['name_with_owner']} ({top_project['stars']:,} stars)")
        
        return {
            "total_projects": len(all_projects),
            "total_stars": total_stars,
            "checked_users": total_users_checked,
            "successful_users": total_users_successful,
            "filtered_users": total_users_filtered,
            "failed_users": total_users_failed,
            "failure_reasons": aggregated_failures,
            "projects": all_projects,
            "collected_at": datetime.now(SEATTLE_TZ).isoformat()
        }
    
    def save_results(self, results: Dict[str, Any], output_file: str):
        """
        Save aggregated results to JSON file
        
        Args:
            results: Aggregated results
            output_file: Output file path
        """
        print(f"\n💾 Step 6: Saving results...")
        
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved to: {output_file}")
    
    def collect(
        self,
        max_users: int = 1000,
        start_user: int = 0,
        output_file: str = None
    ) -> Dict[str, Any]:
        """
        Main collection workflow with support for segmented collection
        
        Args:
            max_users: Maximum users to search
            start_user: Starting user index (for segmented collection)
            output_file: Output file path (optional)
            
        Returns:
            Collection results
        """
        print(f"🚀 Starting Distributed Collection with Multi-Token Support")
        print(f"=" * 60)
        print(f"Max Users: {max_users}")
        print(f"Start User: {start_user}")
        print(f"Batch Size: {self.batch_size}")
        print(f"Auto-manage Workers: {self.auto_manage_workers}")
        print(f"=" * 60)
        
        start_time = time.time()
        
        try:
            # Step 0: Ensure workers are running
            if self.auto_manage_workers:
                self.start_workers()
            else:
                active_workers = self.check_workers()
                if active_workers == 0:
                    print("⚠️  Warning: No workers detected!")
                    print("   Please start workers manually or enable auto-manage-workers")
                    raise ValueError("No workers available")
                print(f"✅ Found {active_workers} active workers")
            
            # Step 1: Check for existing user data or search users
            usernames = self.load_or_search_users(max_users, start_user)
            
            if not usernames:
                raise ValueError("No users found")
            
            # Step 2: Create batches
            batches = self.create_batches(usernames)
            
            # Step 3: Distribute tasks
            result = self.distribute_tasks(batches)
            
            # Step 4: Monitor progress
            self.monitor_progress(result, len(batches))
            
            # Step 4.5: Retry failed tasks
            result = self.retry_failed_tasks(result, batches)
            
            # Step 5: Aggregate results
            aggregated = self.aggregate_results(result)
            
            # Step 6: Save results
            if output_file:
                self.save_results(aggregated, output_file)
            
            # Summary
            elapsed = time.time() - start_time
            print(f"\n" + "=" * 60)
            print(f"✅ Collection Complete!")
            print(f"=" * 60)
            print(f"Total Time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
            print(f"Projects: {aggregated['total_projects']}")
            print(f"Stars: {aggregated['total_stars']:,}")
            print(f"Users: {aggregated['successful_users']} successful, "
                  f"{aggregated['filtered_users']} filtered, "
                  f"{aggregated['failed_users']} failed")
            print(f"=" * 60)
            
            return aggregated
            
        except Exception as e:
            print(f"\n❌ Error during collection: {e}")
            raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Distributed Seattle project collector using Celery workers with multi-token support"
    )
    parser.add_argument(
        "--max-users",
        type=int,
        default=50000,
        help="Maximum number of users to search (default: 50000 for all Seattle users)"
    )
    parser.add_argument(
        "--start-user",
        type=int,
        default=0,
        help="Starting user index for segmented collection (default: 0)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of users per worker batch (default: 50)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file path (default: data/seattle_projects_<timestamp>.json)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of Celery workers to start (default: 8)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="Number of concurrent tasks per worker (default: 2)"
    )
    parser.add_argument(
        "--no-auto-workers",
        action="store_true",
        help="Disable automatic worker management (you must start workers manually)"
    )
    
    args = parser.parse_args()
    
    # Default output file
    if not args.output:
        timestamp = datetime.now(SEATTLE_TZ).strftime("%Y%m%d_%H%M%S")
        args.output = f"data/seattle_projects_{timestamp}.json"
    
    # Check environment
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    # Determine auto-manage workers
    auto_manage = not args.no_auto_workers
    
    if auto_manage:
        print(f"\n✨ Auto-manage workers: ENABLED")
        print(f"   Will automatically start {args.workers} workers if needed")
    else:
        print(f"\n⚠️  Auto-manage workers: DISABLED")
        print(f"   Make sure {args.workers} Celery workers are running!")
        print(f"   Use: python3 -m celery -A distributed.workers.collection_worker worker --loglevel=info --concurrency=2 -n workerN@%h")
    
    print(f"\n🚀 Starting collection now...\n")
    
    # Run collection with auto-worker management
    collector = DistributedCollector(
        batch_size=args.batch_size,
        auto_manage_workers=auto_manage,
        num_workers=args.workers,
        concurrency=args.concurrency
    )
    
    try:
        results = collector.collect(
            max_users=args.max_users,
            start_user=args.start_user,
            output_file=args.output
        )
        
        print(f"\n✅ Success! Results saved to: {args.output}")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Collection interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
