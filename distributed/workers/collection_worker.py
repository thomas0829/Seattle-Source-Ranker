"""
Distributed collection worker using Celery
Each worker fetches repositories for a batch of users in parallel
"""
import os
import sys
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from celery import Task

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.celery_config import celery_app


@celery_app.task(
    bind=True,
    name="workers.collection_worker.fetch_users_batch",
    max_retries=3,
    time_limit=1800,  # 30 minutes hard limit
    soft_time_limit=1500,  # 25 minutes soft limit
)
def fetch_users_batch_task(self, usernames: List[str]) -> Dict[str, Any]:
    """
    Fetch repos for a batch of users using REST API
    Processes each user sequentially within this task
    
    Args:
        usernames: List of GitHub usernames
        
    Returns:
        Dict with aggregated results
    """
    all_repos = []
    successful = 0
    failed = 0
    
    # Use TokenManager for dynamic token selection
    from utils.token_manager import get_token_manager
    use_token_manager = False
    tm = None
    
    try:
        tm = get_token_manager()
        print(f"✅ Using TokenManager with {tm.get_token_count()} tokens (dynamic selection)")
        use_token_manager = True
    except Exception as e:
        # Fallback to single token
        print(f"⚠️  TokenManager not available, falling back to single token: {e}")
        fallback_token = os.getenv("GITHUB_TOKEN")
        if not fallback_token:
            print(f"❌ GITHUB_TOKEN not found in worker environment!")
            return {
                "batch_size": len(usernames),
                "successful_users": 0,
                "failed_users": len(usernames),
                "total_repos": 0,
                "repos": [],
                "completed_at": datetime.utcnow().isoformat()
            }
        print(f"✅ Using single token (length: {len(fallback_token)})")
    
    # Track failure reasons
    failure_reasons = {
        "user_not_found": 0,
        "rate_limit": 0,
        "api_error": 0,
        "exception": 0
    }
    
    print(f"🔄 Processing batch of {len(usernames)} users...")
    
    # Process each user in this batch sequentially using REST API
    for idx, username in enumerate(usernames, 1):
        try:
            print(f"📦 [{idx}/{len(usernames)}] Fetching repos for: {username}", flush=True)
            
            # Get best available token dynamically
            if use_token_manager:
                token = tm.get_token()  # Uses cached rate limit data (60s cache)
            else:
                token = fallback_token
            
            headers = {
                "Authorization": f"token {token}",
            }
            
            user_repos = []
            page = 1
            user_fetch_failed = False
            
            # Fetch all repos for this user (with pagination)
            while True:
                # REST API endpoint for user repos
                repos_url = f"https://api.github.com/users/{username}/repos"
                params = {
                    "type": "owner",
                    "per_page": 100,
                    "page": page,
                    "sort": "stargazers",
                    "direction": "desc"
                }
                
                # Small delay to avoid secondary rate limit (reduced to 0.05s)
                # With token rotation, we can be more aggressive
                time.sleep(0.05)
                
                response = requests.get(repos_url, headers=headers, params=params, timeout=10)
                
                # Handle rate limits - check all tokens and wait for the earliest recovery
                remaining = int(response.headers.get('X-RateLimit-Remaining', 999))
                if remaining < 10:
                    failure_reasons["rate_limit"] += 1
                    
                    if use_token_manager:
                        # Check all tokens to find the earliest reset time
                        min_reset_time = float('inf')
                        token_status = []
                        
                        for i in range(tm.get_token_count()):
                            check_token = tm._tokens[i]
                            check_headers = {'Authorization': f'token {check_token}'}
                            try:
                                check_response = requests.get('https://api.github.com/rate_limit', 
                                                            headers=check_headers, timeout=5)
                                if check_response.status_code == 200:
                                    data = check_response.json()
                                    core = data['resources']['core']
                                    token_remaining = core['remaining']
                                    token_reset = core['reset']
                                    token_status.append(f"Token{i+1}:{token_remaining}/{core['limit']}")
                                    
                                    # Find token with earliest reset that has quota
                                    if token_remaining > 100:
                                        # This token is available now!
                                        min_reset_time = 0
                                        break
                                    elif token_reset < min_reset_time:
                                        min_reset_time = token_reset
                            except Exception as e:
                                print(f"⚠️  Failed to check token {i+1}: {e}")
                        
                        if min_reset_time == 0:
                            # Found available token, refresh and continue immediately
                            print(f"✅ Found available token, continuing... ({', '.join(token_status)})")
                            token = tm.get_token(force_check=True)
                            headers["Authorization"] = f"token {token}"
                        elif min_reset_time != float('inf'):
                            # Wait for earliest token recovery + 60s buffer
                            wait_time = max(min_reset_time - time.time(), 0) + 60
                            print(f"⏳ All tokens low, waiting {wait_time:.0f}s for earliest recovery...")
                            print(f"   Status: {', '.join(token_status)}")
                            time.sleep(wait_time)
                            # After sleep, force refresh to get the recovered token
                            token = tm.get_token(force_check=True)
                            headers["Authorization"] = f"token {token}"
                        else:
                            # Fallback: use current token's reset time
                            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                            wait_time = max(reset_time - time.time(), 0) + 60
                            print(f"⏳ Rate limit low ({remaining}), waiting {wait_time:.0f}s...")
                            time.sleep(wait_time)
                    else:
                        # Fallback for single token mode
                        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                        wait_time = max(reset_time - time.time(), 0) + 60
                        print(f"⏳ Rate limit low ({remaining}), waiting {wait_time:.0f}s...")
                        time.sleep(wait_time)
                    continue
                
                if response.status_code == 403:
                    print(f"⚠️  403 Forbidden for {username}, waiting...")
                    failure_reasons["rate_limit"] += 1
                    time.sleep(10)
                    failed += 1
                    user_fetch_failed = True
                    break
                
                if response.status_code == 404:
                    # User not found
                    failed += 1
                    user_fetch_failed = True
                    failure_reasons["user_not_found"] += 1
                    break
                
                if response.status_code != 200:
                    print(f"❌ API error for {username}: Status {response.status_code}")
                    failed += 1
                    user_fetch_failed = True
                    failure_reasons["api_error"] += 1
                    break
                
                repos = response.json()
                
                if not repos:
                    # No more repos
                    break
                
                # Get user info from first repo's owner data
                user_data = {}
                if repos and len(repos) > 0:
                    owner = repos[0].get("owner", {})
                    user_data = {
                        "login": owner.get("login", username),
                        "type": owner.get("type"),
                    }
                
                # Process repos
                for repo in repos:
                    # Skip forks and archived
                    if repo.get("fork") or repo.get("archived"):
                        continue
                    
                    user_repos.append({
                        "name_with_owner": repo["full_name"],
                        "name": repo["name"],
                        "description": repo.get("description"),
                        "url": repo["html_url"],
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "watchers": repo["watchers_count"],
                        "language": repo.get("language"),
                        "topics": [],  # Will be populated later with individual repo API calls
                        "created_at": repo["created_at"],
                        "updated_at": repo["updated_at"],
                        "pushed_at": repo.get("pushed_at"),
                        "open_issues": repo.get("open_issues_count", 0),
                        "has_issues": repo.get("has_issues", False),
                        "owner": {
                            "login": user_data.get("login", username),
                            "type": user_data.get("type"),
                        }
                    })
                
                # Check if there are more pages
                if len(repos) < 100:
                    break
                
                page += 1
            
            # Fetch topics for each repo (batch enrichment)
            if user_repos and not user_fetch_failed:
                print(f"   📚 Fetching topics for {len(user_repos)} repos...", flush=True)
                for repo_idx, repo_data in enumerate(user_repos):
                    try:
                        # Get fresh token for each request
                        if use_token_manager:
                            token = tm.get_token()
                        else:
                            token = fallback_token
                        
                        headers = {
                            "Authorization": f"token {token}",
                        }
                        
                        # Small delay to avoid rate limiting
                        time.sleep(0.05)
                        
                        # Fetch individual repo to get topics
                        repo_url = f"https://api.github.com/repos/{repo_data['name_with_owner']}"
                        response = requests.get(repo_url, headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            full_repo = response.json()
                            repo_data["topics"] = full_repo.get("topics", [])
                        else:
                            repo_data["topics"] = []
                        
                    except Exception as e:
                        print(f"      ⚠️  Failed to get topics for {repo_data['name']}: {e}")
                        repo_data["topics"] = []
            
            # Mark as successful if we got repos and didn't fail
            if not user_fetch_failed:
                all_repos.extend(user_repos)
                successful += 1
                print(f"   ✅ Got {len(user_repos)} repos from {username}", flush=True)
            
        except Exception as e:
            print(f"❌ Exception fetching repos for {username}: {type(e).__name__}: {e}")
            failed += 1
            failure_reasons["exception"] += 1
            continue
    
    # Print failure summary for this batch
    if failed > 0:
        print(f"\n📊 Batch Failure Summary:")
        print(f"   User not found/inaccessible: {failure_reasons['user_not_found']}")
        print(f"   Rate limit hits: {failure_reasons['rate_limit']}")
        print(f"   API errors: {failure_reasons['api_error']}")
        print(f"   Exceptions: {failure_reasons['exception']}")
    
    return {
        "batch_size": len(usernames),
        "successful_users": successful,
        "failed_users": failed,
        "total_repos": len(all_repos),
        "repos": all_repos,
        "failure_reasons": failure_reasons,
        "completed_at": datetime.utcnow().isoformat()
    }


@celery_app.task(
    name="workers.collection_worker.search_seattle_users",
)
def search_seattle_users_task(max_users: int = 1000) -> List[str]:
    """
    Search for Seattle developers using REST API
    Returns list of usernames to be processed by workers
    
    Args:
        max_users: Maximum number of users to find
        
    Returns:
        List of GitHub usernames
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    usernames = []
    page = 1
    per_page = 100
    
    print(f"🔍 Searching for Seattle developers (target: {max_users})...")
    
    while len(usernames) < max_users:
        url = f"https://api.github.com/search/users"
        params = {
            "q": "location:seattle",
            "per_page": per_page,
            "page": page,
            "sort": "repositories",
            "order": "desc"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ Error searching users: {response.status_code}")
            break
        
        data = response.json()
        users = data.get("items", [])
        
        if not users:
            break
        
        for user in users:
            usernames.append(user["login"])
            if len(usernames) >= max_users:
                break
        
        page += 1
    
    print(f"✅ Found {len(usernames)} Seattle developers")
    return usernames


@celery_app.task(
    name="workers.collection_worker.collect_seattle_projects",
    bind=True,
)
def collect_seattle_projects_task(
    self,
    target_projects: int = 10000,
    max_users: int = 1000,
    batch_size: int = 10,
) -> Dict[str, Any]:
    """
    Main coordinator task for distributed collection
    
    Args:
        target_projects: Target number of projects to collect
        max_users: Maximum users to search
        batch_size: Number of users per worker batch
        
    Returns:
        Collection summary
    """
    from celery import group
    
    print(f"🚀 Starting distributed collection")
    print(f"   Target: {target_projects} projects")
    print(f"   Max users: {max_users}")
    print(f"   Batch size: {batch_size} users/batch")
    
    # Step 1: Search for Seattle users (fast, REST API)
    usernames = search_seattle_users_task()
    
    if not usernames:
        return {
            "success": False,
            "error": "No users found",
            "total_projects": 0
        }
    
    # Step 2: Split users into batches
    user_batches = [
        usernames[i:i + batch_size]
        for i in range(0, len(usernames), batch_size)
    ]
    
    print(f"📦 Split {len(usernames)} users into {len(user_batches)} batches")
    
    # Step 3: Distribute batches to workers (parallel)
    job = group(fetch_users_batch_task.s(batch) for batch in user_batches)
    result = job.apply_async()
    
    print(f"⚡ Spawned {len(user_batches)} parallel tasks")
    print(f"   Waiting for workers to complete...")
    
    # Step 4: Wait and aggregate results
    batch_results = result.get(timeout=1800)  # 30 minutes timeout
    
    all_projects = []
    for batch_result in batch_results:
        all_projects.extend(batch_result["repos"])
    
    # Step 5: Sort by stars and limit
    all_projects.sort(key=lambda x: x["stars"], reverse=True)
    all_projects = all_projects[:target_projects]
    
    total_stars = sum(p["stars"] for p in all_projects)
    
    print(f"\n✅ Collection complete!")
    print(f"   Total projects: {len(all_projects)}")
    print(f"   Total stars: {total_stars:,}")
    
    return {
        "success": True,
        "total_projects": len(all_projects),
        "total_stars": total_stars,
        "total_users": len(usernames),
        "total_batches": len(user_batches),
        "projects": all_projects,
        "completed_at": datetime.utcnow().isoformat()
    }
