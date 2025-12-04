#!/usr/bin/env python3
"""
Secondary Data Update - Validate and enrich repository data using Celery + Redis.

This script serves as a second-stage validation and data enrichment tool:
1. Updates watchers field with real subscribers count (not duplicate of stars)
2. Removes repos that are deleted, private, or blocked (HTTP 451)
3. Validates all repos are still accessible
4. Recalculates total stars after removing invalid repos

Uses Celery workers with Redis for distributed processing.

Usage:
    # First start Redis
    redis-server --daemonize yes

    # Then start workers
    bash scripts/start_workers.sh

    # Finally run this script
    python3 scripts/secondary_update.py [input_file]

If no input file is provided, uses the latest seattle_projects_*.json file.
"""

import json
import os
import sys
import time
import signal
import atexit
from pathlib import Path
from celery import group

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from distributed.workers.collection_worker import update_watchers_batch_task

# Global flag for cleanup
_workers_started_by_script = False

def cleanup_workers():
    """Stop workers if they were started by this script"""
    global _workers_started_by_script
    if _workers_started_by_script:
        print("\n[CLEANUP] Stopping workers...")
        import subprocess
        stop_script = Path(__file__).parent / 'stop_workers.sh'
        if stop_script.exists():
            try:
                subprocess.run(['bash', str(stop_script)], check=False)
            except:
                pass

def signal_handler(signum, frame):
    """Handle Ctrl+C and other signals"""
    print("\n[INTERRUPT] Received signal, cleaning up...")
    global _workers_started_by_script
    if _workers_started_by_script:
        print("[CLEANUP] Stopping workers...")
        import subprocess
        stop_script = Path(__file__).parent / 'stop_workers.sh'
        if stop_script.exists():
            try:
                # Run and wait for workers to stop
                result = subprocess.run(['bash', str(stop_script)], 
                                      check=False, 
                                      capture_output=True, 
                                      text=True,
                                      timeout=30)
                print(result.stdout)
                if result.returncode == 0:
                    print("[OK] Workers stopped successfully")
                else:
                    print(f"[WARNING] Workers may not have stopped cleanly: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("[WARNING] Worker shutdown timed out")
            except Exception as e:
                print(f"[ERROR] Failed to stop workers: {e}")
    sys.exit(1)

# Register cleanup handlers
atexit.register(cleanup_workers)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def secondary_update(input_file=None, batch_size=50):
    """
    Main function to orchestrate secondary data update using Celery workers.

    Args:
        input_file: Path to input JSON file (optional)
        batch_size: Number of repos per batch
    """
    # Find input file
    if input_file is None:
        data_dir = Path(__file__).parent.parent / 'data'
        json_files = sorted(data_dir.glob('seattle_projects_*.json'))
        if not json_files:
            print("[ERROR] No project files found in data/")
            return
        input_file = json_files[-1]
        print(f"[DIR] Using latest file: {input_file.name}")
    else:
        input_file = Path(input_file)

    if not input_file.exists():
        print(f"[ERROR] File not found: {input_file}")
        return

    # Load projects
    print(f"📥 Loading projects from {input_file.name}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    projects = data.get('projects', [])
    print(f"[OK] Loaded {len(projects):,} projects")
    print()

    # Prepare batches
    batches = []
    for i in range(0, len(projects), batch_size):
        batch = projects[i:i + batch_size]
        batches.append(batch)

    total_batches = len(batches)
    print(f"[PKG] Split into {total_batches:,} batches ({batch_size} repos each)")
    print("[START] Dispatching tasks to Celery workers...")
    print()

    # Create task group
    job = group(update_watchers_batch_task.s(batch) for batch in batches)

    # Execute tasks
    start_time = time.time()
    result = job.apply_async()

    # Monitor progress
    print("[WAIT] Processing batches...")
    print()

    last_completed = 0
    while not result.ready():
        # Count completed tasks
        completed = sum(1 for r in result.results if r.ready())

        if completed > last_completed:
            percent = (completed / total_batches) * 100
            elapsed = time.time() - start_time
            rate = completed / elapsed if elapsed > 0 else 0
            remaining = total_batches - completed
            eta = remaining / rate if rate > 0 else 0

            print(f"   Progress: {completed}/{total_batches} ({percent:.1f}%) | "
                  f"Rate: {rate:.1f} batches/sec | ETA: {eta:.0f}s")
            last_completed = completed

        time.sleep(2)

    # Get results
    print()
    print("[STATS] Collecting results...")
    batch_results = result.get()

    # Aggregate results
    updated_count = 0
    unchanged_count = 0
    deleted_count = 0
    repos_to_remove = []

    # Flatten results
    all_results = {}
    for batch_result in batch_results:
        if batch_result:
            all_results.update(batch_result)

    # Update projects
    for idx, project in enumerate(projects):
        owner = project['owner']['login'] if isinstance(project['owner'], dict) else project['owner']
        repo_name = project['name']
        repo_key = f"{owner}/{repo_name}"

        if repo_key in all_results:
            watchers_count = all_results[repo_key]
            old_watchers = project.get('watchers', 0)

            if watchers_count is None:
                # Repo deleted/inaccessible
                deleted_count += 1
                repos_to_remove.append(idx)
            elif watchers_count != old_watchers:
                project['watchers'] = watchers_count
                updated_count += 1
            else:
                unchanged_count += 1

    # Remove deleted repos
    if repos_to_remove:
        print()
        print(f"[DELETE] Removing {len(repos_to_remove)} inaccessible repos...")
        for idx in sorted(set(repos_to_remove), reverse=True):
            if idx < len(projects):
                removed = projects.pop(idx)
                owner = removed['owner']['login'] if isinstance(removed['owner'], dict) else removed['owner']
                print(f"   [ERROR] {owner}/{removed['name']}")

        # Update metadata
        data['total_projects'] = len(projects)
        data['total_stars'] = sum(p.get('stars', 0) for p in projects)

    # Summary
    print()
    print("=" * 70)
    print(" Secondary Update Summary")
    print("=" * 70)
    total_projects = len(projects) + deleted_count
    elapsed = time.time() - start_time
    print(f"Total projects (before):  {total_projects:,}")
    print(f"Total projects (after):   {len(projects):,}")
    print(f"Watchers updated:         {updated_count:,} ({updated_count/total_projects*100:.1f}%)")
    print(f"Unchanged:                {unchanged_count:,} ({unchanged_count/total_projects*100:.1f}%)")
    print(f"Deleted/Blocked:          {deleted_count:,} ({deleted_count/total_projects*100:.1f}%)")
    print(f"Time elapsed:             {elapsed/60:.1f} minutes")
    print(f"Processing rate:          {total_projects/elapsed:.1f} repos/sec")
    print("=" * 70)
    print()

    # Save updated data
    print(f"[SAVE] Saving updated data to {input_file.name}...")
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("[OK] Successfully saved!")
    print()
    print(f"[DONE] Secondary update complete! {len(projects):,} verified repos remain.")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Secondary data update: validate repos and update watchers using Celery + Redis'
    )
    parser.add_argument('input_file', nargs='?', help='Input JSON file (default: latest in data/)')
    parser.add_argument('--batch-size', type=int, default=50, help='Repos per batch (default: 50, max: 100)')

    args = parser.parse_args()

    print()
    print("=" * 70)
    print(" Seattle Source Ranker - Secondary Data Update")
    print("=" * 70)
    print()
    print("[CONFIG]  Using Celery + Redis for distributed processing")
    print("[INFO] This will update watchers and remove invalid repos")
    print()

    # Check if Redis and workers are running
    import subprocess
    try:
        result = subprocess.run(
            ['redis-cli', 'ping'],
            capture_output=True,
            text=True,
            timeout=2,
            check=False
        )
        if result.stdout.strip() != 'PONG':
            print("[ERROR] Redis is not running!")
            print("   Start it with: redis-server --daemonize yes")
            return
        print("[OK] Redis is running")
    except (FileNotFoundError, TimeoutError):
        print("[WARNING]  Could not check Redis status")

    # Check Celery workers
    workers_running = False
    try:
        result = subprocess.run(
            ['python3', '-m', 'celery', '-A', 'distributed.workers.collection_worker', 'inspect', 'active'],
            capture_output=True, text=True, timeout=5, cwd=Path(__file__).parent.parent,
            check=False
        )
        if 'worker' in result.stdout:
            count = result.stdout.count('@')
            print(f"[OK] {count} Celery workers detected")
            workers_running = True
        else:
            print("[WARNING] No active Celery workers found!")
            print("[AUTO] Starting workers automatically...")
            # Auto-start workers
            global _workers_started_by_script
            start_script = Path(__file__).parent / 'start_workers.sh'
            if start_script.exists():
                subprocess.run(['bash', str(start_script)], check=True)
                print("[OK] Workers started successfully")
                workers_running = True
            else:
                print("[ERROR] start_workers.sh not found!")
                print("   Please start manually: bash scripts/start_workers.sh")
                return
    except (FileNotFoundError, TimeoutError):
        print("[WARNING] Could not check Celery worker status")
        print("[AUTO] Attempting to start workers...")
        start_script = Path(__file__).parent / 'start_workers.sh'
        if start_script.exists():
            try:
                subprocess.run(['bash', str(start_script)], check=True)
                print("[OK] Workers started successfully")
                workers_running = True
                _workers_started_by_script = True
            except Exception as e:
                print(f"[ERROR] Failed to start workers: {e}")
                return

    if not workers_running:
        print("[ERROR] Cannot proceed without workers!")
        return

    print()

    secondary_update(args.input_file, args.batch_size)


if __name__ == '__main__':
    main()
