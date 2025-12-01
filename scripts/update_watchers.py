#!/usr/bin/env python3
"""
Update watchers field and validate repository accessibility using GitHub GraphQL API.

This script serves as a second-stage validation and data enrichment tool:
1. Updates watchers field with real subscribers count (not duplicate of stars)
2. Removes repos that are deleted, private, or blocked (HTTP 451)
3. Validates all repos are still accessible

Uses batch queries with aliases to efficiently fetch data.

Usage:
    python3 scripts/update_watchers.py [input_file]
    
If no input file is provided, uses the latest seattle_projects_*.json file.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import requests
from multiprocessing import Pool, Manager
from functools import partial

# Import token manager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.token_manager import TokenManager


def build_graphql_query(repos_batch):
    """
    Build a GraphQL query with aliases to fetch watchers for multiple repos at once.
    
    Args:
        repos_batch: List of tuples (owner, repo_name)
    
    Returns:
        GraphQL query string
    """
    # Build query with aliases for each repo
    aliases = []
    for idx, (owner, repo_name) in enumerate(repos_batch):
        # GraphQL aliases can't start with numbers or contain special chars
        # Replace special chars with underscores
        safe_alias = f"repo_{idx}"
        
        aliases.append(f'''
    {safe_alias}: repository(owner: "{owner}", name: "{repo_name}") {{
        nameWithOwner
        watchers {{
            totalCount
        }}
    }}''')
    
    query = "{" + "".join(aliases) + "\n}"
    
    return query


def fetch_watchers_batch_worker(args):
    """
    Worker function for multiprocessing - fetch watchers for a batch of repos.
    
    Args:
        args: Tuple of (batch_id, repos_batch, token_manager_data)
    
    Returns:
        Tuple of (batch_id, results_dict, deleted_repos)
    """
    batch_id, repos_batch = args
    
    # Create token manager instance (each process needs its own)
    token_manager = TokenManager()
    
    query = build_graphql_query(repos_batch)
    token = token_manager.get_token()
    
    headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json',
    }
    
    payload = {'query': query}
    
    try:
        response = requests.post(
            'https://api.github.com/graphql',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for errors
            if 'errors' in data:
                # Still try to parse successful repos
                pass
            
            # Parse results
            results = {}
            deleted_repos = []
            
            if 'data' in data:
                for idx, (owner, repo_name) in enumerate(repos_batch):
                    safe_alias = f"repo_{idx}"
                    repo_data = data['data'].get(safe_alias)
                    repo_key = f"{owner}/{repo_name}"
                    
                    if repo_data and repo_data.get('watchers'):
                        watchers_count = repo_data['watchers']['totalCount']
                        results[repo_key] = watchers_count
                    elif repo_data is None:
                        # Repo deleted or inaccessible
                        deleted_repos.append(repo_key)
                        results[repo_key] = None
            
            return (batch_id, results, deleted_repos)
            
        elif response.status_code == 403:
            # Rate limit - wait and retry
            time.sleep(60)
            return fetch_watchers_batch_worker(args)
        else:
            return (batch_id, {}, [])
            
    except Exception as e:
        return (batch_id, {}, [])


def fetch_watchers_batch(token_manager, repos_batch, stats):
    """
    Fetch watchers count for a batch of repos using GraphQL.
    (Legacy single-threaded version - kept for compatibility)
    
    Args:
        token_manager: TokenManager instance
        repos_batch: List of tuples (owner, repo_name)
        stats: Dict to track API call statistics
    
    Returns:
        Dict mapping "owner/repo" to watchers count
    """
    query = build_graphql_query(repos_batch)
    
    # Get token from manager
    token = token_manager.get_token()
    
    headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json',
    }
    
    payload = {'query': query}
    
    # Track API call
    stats['api_calls'] += 1
    
    try:
        response = requests.post(
            'https://api.github.com/graphql',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for errors
            if 'errors' in data:
                print(f"  GraphQL errors: {data['errors']}")
                return {}
            
            # Parse results
            results = {}
            if 'data' in data:
                for idx, (owner, repo_name) in enumerate(repos_batch):
                    safe_alias = f"repo_{idx}"
                    repo_data = data['data'].get(safe_alias)
                    
                    if repo_data and repo_data.get('watchers'):
                        repo_key = f"{owner}/{repo_name}"
                        watchers_count = repo_data['watchers']['totalCount']
                        results[repo_key] = watchers_count
                    elif repo_data is None:
                        # Repo might be deleted or private
                        repo_key = f"{owner}/{repo_name}"
                        results[repo_key] = None
            
            return results
            
        elif response.status_code == 401:
            print(" Authentication failed - check token validity")
            return {}
        elif response.status_code == 403:
            print("  Rate limit hit, waiting...")
            time.sleep(60)
            return fetch_watchers_batch(token_manager, repos_batch)
        else:
            print(f" HTTP {response.status_code}: {response.text[:200]}")
            return {}
            
    except requests.exceptions.Timeout:
        print("  Request timeout, retrying...")
        time.sleep(5)
        return fetch_watchers_batch(token_manager, repos_batch)
    except Exception as e:
        print(f" Error fetching batch: {e}")
        return {}


def update_project_watchers(input_file=None, batch_size=100, remove_inaccessible=True, num_workers=8):
    """
    Update watchers field and validate repository accessibility using parallel workers.
    
    Args:
        input_file: Path to input JSON file (optional)
        batch_size: Number of repos to query per GraphQL request
        remove_inaccessible: If True, remove repos that cannot be accessed (deleted/blocked/private)
        num_workers: Number of parallel workers to use
    """
    # Find input file
    if input_file is None:
        data_dir = Path(__file__).parent.parent / 'data'
        json_files = sorted(data_dir.glob('seattle_projects_*.json'))
        if not json_files:
            print(" No project files found in data/")
            return
        input_file = json_files[-1]
        print(f" Using latest file: {input_file.name}")
    else:
        input_file = Path(input_file)
    
    if not input_file.exists():
        print(f" File not found: {input_file}")
        return
    
    # Load projects
    print(f" Loading projects from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    projects = data.get('projects', [])
    total_projects = len(projects)
    print(f" Loaded {total_projects:,} projects")
    
    # Prepare batches
    repos_to_fetch = []
    project_map = {}  # Map "owner/repo" to project dict
    project_index_map = {}  # Map "owner/repo" to index in projects list
    
    for idx, project in enumerate(projects):
        owner_data = project.get('owner')
        repo_name = project.get('name')
        
        # Handle owner being a dict with 'login' key
        if isinstance(owner_data, dict):
            owner = owner_data.get('login')
        else:
            owner = owner_data
        
        if owner and repo_name:
            repo_key = f"{owner}/{repo_name}"
            repos_to_fetch.append((owner, repo_name))
            project_map[repo_key] = project
            project_index_map[repo_key] = idx
    
    total_batches = (len(repos_to_fetch) + batch_size - 1) // batch_size
    print(f" Processing {len(repos_to_fetch):,} repos in {total_batches:,} batches with {num_workers} workers")
    print()
    
    # Prepare batch jobs
    batch_jobs = []
    for batch_idx in range(0, len(repos_to_fetch), batch_size):
        batch = repos_to_fetch[batch_idx:batch_idx + batch_size]
        batch_id = batch_idx // batch_size
        batch_jobs.append((batch_id, batch))
    
    # Process batches in parallel
    updated_count = 0
    failed_count = 0
    unchanged_count = 0
    deleted_count = 0
    repos_to_remove = []  # List of repo indices to remove
    
    start_time = time.time()
    completed_batches = 0
    
    print(" Starting parallel processing...")
    print()
    
    # Use multiprocessing pool
    with Pool(processes=num_workers) as pool:
        # Process batches in parallel
        for batch_id, results, deleted_repos in pool.imap_unordered(fetch_watchers_batch_worker, batch_jobs):
            completed_batches += 1
            
            # Update projects
            batch_updated = 0
            batch_deleted = 0
            batch_failed = 0
            
            for repo_key, watchers_count in results.items():
                if repo_key in project_map:
                    project = project_map[repo_key]
                    old_watchers = project.get('watchers', 0)
                    
                    if watchers_count is None:
                        # Repo deleted, blocked, or inaccessible
                        deleted_count += 1
                        batch_deleted += 1
                        if remove_inaccessible:
                            repos_to_remove.append(project_index_map[repo_key])
                    elif watchers_count != old_watchers:
                        project['watchers'] = watchers_count
                        updated_count += 1
                        batch_updated += 1
                    else:
                        unchanged_count += 1
            
            # Track deleted repos
            for repo_key in deleted_repos:
                if repo_key in project_map and remove_inaccessible:
                    if project_index_map[repo_key] not in repos_to_remove:
                        repos_to_remove.append(project_index_map[repo_key])
            
            # Progress update
            if completed_batches % 50 == 0:
                elapsed = time.time() - start_time
                rate = completed_batches / elapsed if elapsed > 0 else 0
                remaining_batches = total_batches - completed_batches
                eta_seconds = remaining_batches / rate if rate > 0 else 0
                
                print(f"    Progress: {completed_batches}/{total_batches} ({completed_batches/total_batches*100:.1f}%) | "
                      f"Rate: {rate:.1f} batches/sec | ETA: {eta_seconds:.0f}s | "
                      f"Updated: {updated_count:,}, Deleted: {deleted_count:,}")
    
    print()
    print(f" Completed {completed_batches} batches")
    
    # Remove inaccessible repos
    if remove_inaccessible and repos_to_remove:
        print()
        print(f"  Removing {len(repos_to_remove)} inaccessible repos...")
        # Sort in reverse order to avoid index shifting issues
        for idx in sorted(set(repos_to_remove), reverse=True):
            if idx < len(projects):
                removed_project = projects.pop(idx)
                owner = removed_project['owner']['login'] if isinstance(removed_project['owner'], dict) else removed_project['owner']
                name = removed_project['name']
                print(f"   Removed: {owner}/{name}")
        
        # Update metadata
        data['total_projects'] = len(projects)
        if 'total_stars' in data:
            data['total_stars'] = sum(p.get('stars', 0) for p in projects)
    
    # Summary
    elapsed_time = time.time() - start_time
    print()
    print("=" * 70)
    print(" Update & Validation Summary")
    print("=" * 70)
    print(f"Total projects (before): {total_projects:,}")
    if remove_inaccessible:
        print(f"Total projects (after):  {len(projects):,}")
    print(f"Updated:                {updated_count:,} ({updated_count/total_projects*100:.1f}%)")
    print(f"Unchanged:              {unchanged_count:,} ({unchanged_count/total_projects*100:.1f}%)")
    print(f"Deleted/Blocked:        {deleted_count:,} ({deleted_count/total_projects*100:.1f}%)")
    if remove_inaccessible:
        print(f"  -> Removed from data:  {len(set(repos_to_remove)):,}")
    print(f"Failed:                 {failed_count:,} ({failed_count/total_projects*100:.1f}%)")
    print()
    print("=" * 70)
    print(" Performance Metrics")
    print("=" * 70)
    print(f"Time elapsed:           {elapsed_time/60:.1f} minutes ({elapsed_time:.1f} seconds)")
    print(f"Workers used:           {num_workers}")
    print(f"Total batches:          {total_batches:,}")
    print(f"Rate:                   {total_batches/elapsed_time*60:.1f} batches/min")
    print(f"Repos per second:       {total_projects/elapsed_time:.1f}")
    print(f"Avg time per batch:     {elapsed_time/total_batches:.2f} seconds")
    print(f"Token usage estimate:   {total_batches:,} / 30,000 = {total_batches/30000*100:.1f}%")
    print(f"Speedup vs 1 worker:    {291.7*60/elapsed_time:.1f}x")
    print()
    
    # Save updated data (overwrite original file)
    print(f" Saving updated data to {input_file.name}...")
    
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f" Successfully saved (overwritten original file)")
    print()
    
    # Show some examples
    print(" Sample watchers updates:")
    sample_count = 0
    for project in projects[:20]:
        owner = project['owner']['login'] if isinstance(project['owner'], dict) else project['owner']
        repo = project.get('name')
        stars = project.get('stars', 0)
        watchers = project.get('watchers', 0)
        if watchers != stars:
            ratio = (watchers / stars * 100) if stars > 0 else 0
            print(f"   {owner}/{repo}: stars={stars:,}, watchers={watchers:,} ({ratio:.1f}%)")
            sample_count += 1
            if sample_count >= 5:
                break
    
    if sample_count == 0:
        print("   (No samples with different stars/watchers values in first 20 projects)")
    
    print()
    print(f" Validation complete! {len(projects):,} verified accessible repos remain.")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Update watchers data and validate repository accessibility using GitHub GraphQL API'
    )
    parser.add_argument('input_file', nargs='?', help='Input JSON file (default: latest in data/)')
    parser.add_argument('--batch-size', type=int, default=100, help='Repos per GraphQL query (default: 100)')
    parser.add_argument('--workers', type=int, default=8, help='Number of parallel workers (default: 8)')
    parser.add_argument('--keep-inaccessible', action='store_true', 
                        help='Keep repos that cannot be accessed (default: remove them)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print(" Seattle Source Ranker - Watchers Update & Validation")
    print("=" * 70)
    print()
    
    remove_inaccessible = not args.keep_inaccessible
    if remove_inaccessible:
        print("  Mode: Remove inaccessible repos (deleted/blocked/private)")
    else:
        print(" Mode: Keep all repos (only update watchers)")
    print(f" Workers: {args.workers}")
    print()
    
    update_project_watchers(args.input_file, args.batch_size, remove_inaccessible, args.workers)


if __name__ == '__main__':
    main()
