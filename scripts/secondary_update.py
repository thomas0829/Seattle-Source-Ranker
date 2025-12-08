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
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from seattle_source_ranker.tokens import TokenManager
import atexit
from pathlib import Path
from celery import group
from seattle_source_ranker.utils.progress import monitor_celery_task

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seattle_source_ranker.collector.collection_worker import update_watchers_batch_task

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
    print("\n\n[INTERRUPT] Received interrupt signal...")
    
    # Stop workers if started by this script
    global _workers_started_by_script
    if _workers_started_by_script:
        print("[CLEANUP] Stopping workers...")
        stop_script = Path(__file__).parent / 'stop_workers.sh'
        if stop_script.exists():
            try:
                subprocess.run(['bash', str(stop_script)], 
                              check=False, 
                              capture_output=True, 
                              text=True,
                              timeout=30)
                print("[OK] Workers stopped")
            except Exception as e:
                print(f"[WARNING] Worker stop error: {e}")
    
    # Raise KeyboardInterrupt to trigger finally block
    raise KeyboardInterrupt("User interrupted execution")

# Register cleanup handlers
atexit.register(cleanup_workers)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def flush_redis():
    """Flush Redis to clear all tasks"""
    try:
        result = subprocess.run(['redis-cli', 'FLUSHDB'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            return True
        return False
    except Exception:
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.flushdb()
            return True
        except Exception:
            return False


def secondary_update(input_file=None, batch_size=50):
    """
    Main function to orchestrate secondary data update using Celery workers.

    Args:
        input_file: Path to input JSON file (optional)
        batch_size: Number of repos per batch
    """
    try:
        # Clear any leftover tasks before starting
        print("[INIT] Clearing Redis queue...")
        if flush_redis():
            print("[OK] Redis queue cleared")
        else:
            print("[WARNING] Could not clear Redis queue")
        print()
        
        # Find input file
        if input_file is None:
            data_dir = Path(__file__).parent.parent / 'data'
            input_file = data_dir / 'seattle_projects.json'
            if not input_file.exists():
                print("[ERROR] seattle_projects.json not found in data/")
                return
            print(f"[DIR] Using file: {input_file.name}")
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

        # Record start time for summary
        start_time = time.time()

        # Create task group
        job = group(update_watchers_batch_task.s(batch) for batch in batches)

        # Execute tasks (non-blocking)
        result = job.apply_async()

        # Monitor progress with unified progress bar
        batch_results = monitor_celery_task(
            result=result,
            total_tasks=total_batches,
            desc="Verifying projects",
            check_interval=1.0
        )

        # Aggregate results
        updated_count = 0
        unchanged_count = 0
        deleted_count = 0
        repos_to_remove = []
        
        # Track deletion reasons
        deletion_reasons = {
            'isEmpty': [],
            'isLocked': [],
            'isArchived': [],
            'deleted': [],
            'no_watchers': []
        }

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
                result_data = all_results[repo_key]
                old_watchers = project.get('watchers', 0)

                # Handle different result types
                if isinstance(result_data, dict):
                    status = result_data.get('status')
                    
                    if status == 'filtered':
                        # Repo should be removed (isEmpty/isLocked/isArchived)
                        reasons = result_data.get('reasons', [])
                        deleted_count += 1
                        repos_to_remove.append(idx)
                        
                        # Track each reason
                        for reason in reasons:
                            if reason in deletion_reasons:
                                deletion_reasons[reason].append({
                                    'repo': repo_key,
                                    'stars': project.get('stars', 0)
                                })
                    
                    elif status == 'deleted':
                        # Repo deleted or inaccessible
                        deleted_count += 1
                        repos_to_remove.append(idx)
                        deletion_reasons['deleted'].append({
                            'repo': repo_key,
                            'stars': project.get('stars', 0)
                        })
                    
                    elif status == 'no_watchers':
                        # Repo exists but no watchers data (keep it)
                        deletion_reasons['no_watchers'].append(repo_key)
                        unchanged_count += 1
                
                elif result_data is None:
                    # None means query failed (rate limit/error) - KEEP the repo, don't delete
                    unchanged_count += 1
                
                elif isinstance(result_data, int):
                    # Watchers count update
                    if result_data != old_watchers:
                        project['watchers'] = result_data
                        updated_count += 1
                    else:
                        unchanged_count += 1
                else:
                    unchanged_count += 1

        # Remove deleted repos
        if repos_to_remove:
            print()
            print(f"[DELETE] Removing {len(repos_to_remove)} inaccessible repos...")
            print("   (deleted/private/blocked/empty/locked/archived)")
            
            # Save removed repos to a log file for verification
            removed_log = input_file.parent / 'removed_repos_log.json'
            removed_repos = []
            
            # Build reverse lookup for deletion reasons
            repo_reason_map = {}
            for reason_type, repos_list in deletion_reasons.items():
                if reason_type != 'no_watchers':
                    for repo_info in repos_list:
                        if isinstance(repo_info, dict):
                            repo_key = repo_info['repo']
                            if repo_key not in repo_reason_map:
                                repo_reason_map[repo_key] = []
                            repo_reason_map[repo_key].append(reason_type)
            
            for idx in sorted(set(repos_to_remove), reverse=True):
                if idx < len(projects):
                    removed = projects.pop(idx)
                    owner = removed['owner']['login'] if isinstance(removed['owner'], dict) else removed['owner']
                    repo_name = removed['name']
                    repo_key = f"{owner}/{repo_name}"
                    
                    # Get specific reason(s) for this repo
                    reasons = repo_reason_map.get(repo_key, ['unknown'])
                    reason_str = ', '.join(reasons)
                    
                    removed_repos.append({
                        'name_with_owner': repo_key,
                        'stars': removed.get('stars', 0),
                        'url': removed.get('url', ''),
                        'reason': reason_str
                    })
                    
                    print(f"   [REMOVED] {repo_key} (⭐ {removed.get('stars', 0)}) - {reason_str}")
            
            # Save log
            print(f"\n[LOG] Saving removal log to {removed_log.name}...")
            with open(removed_log, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_removed': len(removed_repos),
                    'removed_repos': removed_repos
                }, f, ensure_ascii=False, indent=2)
            print(f"[OK] Log saved with {len(removed_repos)} entries")

            # Update metadata
            data['total_projects'] = len(projects)
            data['total_stars'] = sum(p.get('stars', 0) for p in projects)

        # Summary with detailed deletion reasons
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
        print()
        print("Deletion Breakdown:")
        for reason, repos_list in deletion_reasons.items():
            if repos_list and reason != 'no_watchers':
                count = len(repos_list)
                print(f"  • {reason:12s}: {count:,} repos ({count/deleted_count*100:.1f}% of deleted)" if deleted_count > 0 else f"  • {reason:12s}: {count:,} repos")
                
                # Show top 3 examples with highest stars
                if isinstance(repos_list[0], dict):
                    top_examples = sorted(repos_list, key=lambda x: x['stars'], reverse=True)[:3]
                    for ex in top_examples:
                        print(f"      - {ex['repo']} (⭐ {ex['stars']:,})")
        
        print()
        print(f"Time elapsed:             {elapsed/60:.1f} minutes")
        print(f"Processing rate:          {total_projects/elapsed:.1f} repos/sec")
        print("=" * 70)
        print()

        # Determine output file - always save to seattle_projects.json (standard filename)
        output_file = input_file.parent / 'seattle_projects.json'
        print(f"[SAVE] Saving updated data to {output_file.name}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("[OK] Successfully saved!")
        print()
        print(f"[DONE] Secondary update complete! {len(projects):,} verified repos remain.")
        print(f"[OUTPUT] Standard filename: {output_file}")
        
    finally:
        # Always clean up Redis on exit
        print()
        print("[CLEANUP] Clearing Redis queue...")
        if flush_redis():
            print("[OK] Redis queue cleared")
        else:
            print("[WARNING] Could not clear Redis queue")


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
            ['python3', '-m', 'celery', '-A', 'seattle_source_ranker.collector.collection_worker', 'inspect', 'active'],
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

    try:
        secondary_update(args.input_file, args.batch_size)
    except KeyboardInterrupt:
        print("\n[EXIT] Interrupted by user")
        sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[EXIT] Interrupted by user")
        sys.exit(0)
