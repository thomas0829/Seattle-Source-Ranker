"""
Distributed Collection Coordinator

Coordinates multiple Celery workers to collect Seattle projects in parallel.
Uses Redis as message broker and PostgreSQL for data persistence.

Usage:
    python3 distributed_collector.py --target 10000 --workers 5 --batch-size 10
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
from typing import List, Dict, Any
from celery import group
from celery.result import GroupResult

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.collection_worker import (
    search_seattle_users_task,
    fetch_users_batch_task,
    collect_seattle_projects_task
)
from utils.celery_config import celery_app


class DistributedCollector:
    """
    Coordinator for distributed data collection
    
    Responsibilities:
    - Search for Seattle developers (REST API)
    - Split developers into batches
    - Distribute batches to workers
    - Monitor progress
    - Aggregate and save results
    """
    
    def __init__(self, batch_size: int = 10, auto_manage_workers: bool = True, num_workers: int = 8):
        """
        Args:
            batch_size: Number of users per worker batch
            auto_manage_workers: Automatically start/stop workers
            num_workers: Number of workers to start if auto_manage_workers is True
        """
        self.batch_size = batch_size
        self.results = []
        self.auto_manage_workers = auto_manage_workers
        self.num_workers = num_workers
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
        log_dir = os.path.join(project_root, "distributed", "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        for i in range(1, self.num_workers + 1):
            log_file = os.path.join(log_dir, f"worker_{i}.log")
            
            # Start worker process
            cmd = [
                sys.executable, "-m", "celery",
                "-A", "distributed.workers.collection_worker",
                "worker",
                "--loglevel=info",
                f"--concurrency=2",
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
        for _ in range(30):  # Wait up to 15 seconds
            time.sleep(0.5)
            active = self.check_workers()
            if active >= self.num_workers:
                print(f" ✅ {active} workers ready!")
                return
            print(".", end="", flush=True)
        
        print(f"\n   ⚠️  Only {self.check_workers()} workers registered (expected {self.num_workers})")
        print(f"   Continuing anyway...")
    
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
            
            # Check if file is less than 3 days old
            file_mtime = os.path.getmtime(filepath)
            age_hours = (time.time() - file_mtime) / 3600
            
            if age_hours < 72:  # Less than 3 days
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
        Search for Seattle developers using REST API with multiple queries to bypass 1000 limit
        
        Args:
            max_users: Maximum number of users to find
            start_user: Starting index for segmented collection
            
        Returns:
            List of GitHub usernames
        """
        import requests
        
        print(f"🔍 Step 1: Searching for Seattle developers...")
        print(f"   Target: {max_users} users (starting from index {start_user})")
        print(f"   Strategy: Multiple queries with repo filters to bypass 1000 limit")
        
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
        
        usernames_set = set()  # Use set to avoid duplicates
        
        # Strategy: Pre-defined optimal filters + dynamic subdivision fallback
        # Use known working filters, auto-split if user counts change over time
        print(f"   Using pre-optimized filters with dynamic fallback")
        
        def get_user_count(repo_filter: str) -> int:
            """Get total user count for a repo filter"""
            url = "https://api.github.com/search/users"
            params = {"q": f"location:seattle {repo_filter}", "per_page": 1}
            
            if use_token_manager:
                current_token = tm.get_token()
            else:
                current_token = token
            
            headers_check = {
                "Authorization": f"token {current_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(url, headers=headers_check, params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get("total_count", 0)
            return 0
        
        def subdivide_range(start: int, end: int) -> List[str]:
            """
            Recursively subdivide a range if it has > 900 users
            Returns list of repo filters that are safe to query
            """
            if start == end:
                repo_filter = f"repos:{start}"
            else:
                repo_filter = f"repos:{start}..{end}"
            
            count = get_user_count(repo_filter)
            print(f"      Checking {repo_filter}: {count} users", end="")
            
            # If under threshold, use this range as-is
            if count <= 900:
                print(f" ✅")
                time.sleep(0.2)
                return [repo_filter]
            
            # If it's a single number and still > 900, try subdividing by followers
            if start == end:
                print(f" 🔄 (trying followers subdivision)")
                time.sleep(0.2)
                
                # Try to subdivide by followers
                followers_ranges = [
                    "followers:>=100",
                    "followers:50..99",
                    "followers:20..49",
                    "followers:10..19",
                    "followers:5..9",
                    "followers:1..4",
                    "followers:0",
                ]
                
                sub_filters = []
                for followers in followers_ranges:
                    sub_filter = f"{repo_filter} {followers}"
                    sub_count = get_user_count(sub_filter)
                    print(f"         {sub_filter}: {sub_count} users", end="")
                    
                    if sub_count <= 900:
                        print(f" ✅")
                        sub_filters.append(sub_filter)
                    else:
                        print(f" ⚠️ (still too many, accepting anyway)")
                        sub_filters.append(sub_filter)
                    
                    time.sleep(0.2)
                
                # Verify we got them all
                return sub_filters if sub_filters else [repo_filter]
            
            # Otherwise, split in half and recurse
            print(f" 🔄 (splitting)")
            mid = (start + end) // 2
            time.sleep(0.2)
            
            left = subdivide_range(start, mid)
            right = subdivide_range(mid + 1, end)
            
            return left + right
        
        # Pre-defined optimal filters (based on testing, valid as of 2025-11-06)
        # Strategy: repos>=10 all users, repos:1-9 only followers>=5 (quality filter)
        # Total: ~28,000 users (24K high-activity + 4K quality low-repo)
        preoptimized_filters = [
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
        
        print(f"   Using {len(preoptimized_filters)} pre-optimized filters")
        print(f"   (Dynamic subdivision available as fallback if counts change)")
        
        repo_ranges = preoptimized_filters
        
        for idx, repo_filter in enumerate(repo_ranges, 1):
            # Don't stop early - collect from all filters to maximize diversity
            # Will truncate to max_users at the end
                
            print(f"   [{idx}/{len(repo_ranges)}] Searching: location:seattle {repo_filter}")
            
            page = 1
            per_page = 100
            query_users = 0
            
            while True:  # Collect all users from this filter (up to 1000)
                # Get fresh token for each request
                if use_token_manager:
                    current_token = tm.get_token()
                else:
                    current_token = token
                
                headers = {
                    "Authorization": f"token {current_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                
                url = f"https://api.github.com/search/users"
                params = {
                    "q": f"location:seattle {repo_filter}",
                    "per_page": per_page,
                    "page": page,
                    "sort": "repositories",
                    "order": "desc"
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code != 200:
                    print(f"      ⚠️ API returned status {response.status_code}, moving to next filter")
                    break
                
                data = response.json()
                users = data.get("items", [])
                
                if not users:
                    break
                
                for user in users:
                    usernames_set.add(user["login"])
                    query_users += 1
                
                print(f"      Page {page}: +{len(users)} users (total in this query: {query_users}, overall: {len(usernames_set)})", end="\r", flush=True)
                
                # Stop if we've hit the 1000 result limit for this query
                if page * per_page >= 1000:
                    print(f"\n      Reached 1000 limit for this filter")
                    break
                
                page += 1
                time.sleep(0.5)  # Rate limit prevention
            
            print()  # New line after query complete
        
        # Convert set to list and truncate to max_users
        usernames = list(usernames_set)[:max_users]
        
        print(f"✅ Found {len(usernames)} unique developers (requested: {max_users})")
        
        # Save usernames list to file in parent data/ directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        usernames_file = os.path.join(project_root, "data", f"seattle_users_{timestamp}.json")
        os.makedirs(os.path.dirname(usernames_file), exist_ok=True)
        
        with open(usernames_file, "w", encoding="utf-8") as f:
            json.dump({
                "total_users": len(usernames),
                "collected_at": datetime.utcnow().isoformat(),
                "query_strategy": "multi-filter with repo counts",
                "filters_used": len(repo_ranges),
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
    
    def aggregate_results(self, result: GroupResult, target_projects: int, checkpoint_file: str = None) -> Dict[str, Any]:
        """
        Aggregate results from all workers with checkpoint saving
        
        Args:
            result: Celery GroupResult
            target_projects: Target number of projects
            checkpoint_file: Optional checkpoint file path for incremental saves
            
        Returns:
            Aggregated results
        """
        print(f"\n📥 Step 5: Aggregating results...")
        
        batch_results = result.get(timeout=3600)  # 60 minutes timeout (increased for large collections)
        
        all_projects = []
        total_users_successful = 0
        total_users_failed = 0
        
        # Aggregate failure reasons
        aggregated_failures = {
            "user_not_found": 0,
            "rate_limit": 0,
            "api_error": 0,
            "exception": 0
        }
        
        for batch_result in batch_results:
            all_projects.extend(batch_result["repos"])
            total_users_successful += batch_result["successful_users"]
            total_users_failed += batch_result["failed_users"]
            
            # Aggregate failure reasons if available
            if "failure_reasons" in batch_result:
                for reason, count in batch_result["failure_reasons"].items():
                    aggregated_failures[reason] += count
        
        print(f"   Raw projects collected: {len(all_projects)}")
        print(f"   Successful users: {total_users_successful}")
        print(f"   Failed users: {total_users_failed}")
        
        if total_users_failed > 0:
            print(f"\n   📊 Failure Analysis:")
            print(f"      User not found/inaccessible: {aggregated_failures['user_not_found']} ({aggregated_failures['user_not_found']/total_users_failed*100:.1f}%)")
            print(f"      Rate limit hits: {aggregated_failures['rate_limit']} ({aggregated_failures['rate_limit']/total_users_failed*100:.1f}%)")
            print(f"      API errors: {aggregated_failures['api_error']} ({aggregated_failures['api_error']/total_users_failed*100:.1f}%)")
            print(f"      Exceptions: {aggregated_failures['exception']} ({aggregated_failures['exception']/total_users_failed*100:.1f}%)")
        
        # Sort by stars and limit
        all_projects.sort(key=lambda x: x["stars"], reverse=True)
        top_projects = all_projects[:target_projects]
        
        total_stars = sum(p["stars"] for p in top_projects)
        
        print(f"\n   Top {len(top_projects)} projects selected")
        print(f"   Total stars: {total_stars:,}")
        
        if top_projects:
            top_project = top_projects[0]
            print(f"   #1 project: {top_project['name_with_owner']} ({top_project['stars']:,} stars)")
        
        return {
            "total_projects": len(top_projects),
            "total_stars": total_stars,
            "successful_users": total_users_successful,
            "failed_users": total_users_failed,
            "failure_reasons": aggregated_failures,
            "projects": top_projects,
            "collected_at": datetime.utcnow().isoformat()
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
        target_projects: int = 10000,
        max_users: int = 1000,
        start_user: int = 0,
        output_file: str = None
    ) -> Dict[str, Any]:
        """
        Main collection workflow with support for segmented collection
        
        Args:
            target_projects: Target number of projects
            max_users: Maximum users to search
            start_user: Starting user index (for segmented collection)
            output_file: Output file path (optional)
            
        Returns:
            Collection results
        """
        print(f"🚀 Starting Distributed Collection with Multi-Token Support")
        print(f"=" * 60)
        print(f"Target Projects: {target_projects}")
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
            aggregated = self.aggregate_results(result, target_projects)
            
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
        "--target",
        type=int,
        default=10000,
        help="Target number of projects to collect (default: 10000)"
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
        help="Output JSON file path (default: data/seattle_projects_distributed_<timestamp>.json)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of Celery workers to start (default: 8)"
    )
    parser.add_argument(
        "--no-auto-workers",
        action="store_true",
        help="Disable automatic worker management (you must start workers manually)"
    )
    
    args = parser.parse_args()
    
    # Default output file
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"data/seattle_projects_distributed_{timestamp}.json"
    
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
        num_workers=args.workers
    )
    
    try:
        results = collector.collect(
            target_projects=args.target,
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
