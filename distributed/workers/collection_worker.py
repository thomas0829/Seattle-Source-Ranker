"""
Distributed collection worker using Celery
Each worker fetches repositories for a batch of users in parallel
"""
import os
import sys
import time
from typing import List, Dict, Any
from datetime import datetime
import requests

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.celery_config import celery_app


@celery_app.task(
    bind=True,
    name="workers.collection_worker.fetch_users_batch",
    max_retries=3,
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
        print("[OK] Using TokenManager with {tm.get_token_count()} tokens (dynamic selection)")
        use_token_manager = True
    except Exception:
        # Fallback to single token
        print("[WARNING]  TokenManager not available, falling back to single token")
        fallback_token = os.getenv("GITHUB_TOKEN")
        if not fallback_token:
            print("[ERROR] GITHUB_TOKEN not found in worker environment!")
            return {
                "batch_size": len(usernames),
                "successful_users": 0,
                "failed_users": len(usernames),
                "total_repos": 0,
                "repos": [],
                "completed_at": datetime.utcnow().isoformat()
            }
        print("[OK] Using single token (length: {len(fallback_token)})")

    # Track failure reasons
    failure_reasons = {
        "user_not_found": 0,
        "rate_limit": 0,
        "api_error": 0,
        "exception": 0,
        "filtered_criteria": 0  # Doesn't meet repos/followers criteria
    }

    successful = 0
    failed = 0
    filtered = 0  # Users filtered out due to criteria
    checked = 0  # Total users checked (for statistics)

    print("[RETRY] Processing batch of {len(usernames)} users...")

    # Process each user in this batch sequentially using REST API
    for idx, username in enumerate(usernames, 1):
        checked += 1  # Count all users we attempt to check
        try:
            print(f"[PKG] [{idx}/{len(usernames)}] Fetching repos for: {username}", flush=True)

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
                                print("[WARNING]  Failed to check token {i+1}: {e}")

                        if min_reset_time == 0:
                            # Found available token, refresh and continue immediately
                            print("[OK] Found available token, continuing... ({', '.join(token_status)})")
                            token = tm.get_token(force_check=True)
                            headers["Authorization"] = f"token {token}"
                        elif min_reset_time != float('inf'):
                            # Wait for earliest token recovery + 60s buffer
                            wait_time = max(min_reset_time - time.time(), 0) + 60
                            print("[WAIT] All tokens low, waiting {wait_time:.0f}s for earliest recovery...")
                            print("   Status: {', '.join(token_status)}")
                            time.sleep(wait_time)
                            # After sleep, force refresh to get the recovered token
                            token = tm.get_token(force_check=True)
                            headers["Authorization"] = f"token {token}"
                        else:
                            # Fallback: use current token's reset time
                            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                            wait_time = max(reset_time - time.time(), 0) + 60
                            print("[WAIT] Rate limit low ({remaining}), waiting {wait_time:.0f}s...")
                            time.sleep(wait_time)
                    else:
                        # Fallback for single token mode
                        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                        wait_time = max(reset_time - time.time(), 0) + 60
                        print("[WAIT] Rate limit low ({remaining}), waiting {wait_time:.0f}s...")
                        time.sleep(wait_time)
                    continue

                if response.status_code == 403:
                    print("[WARNING]  403 Forbidden for {username}, waiting...")
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
                    print("[ERROR] API error for {username}: Status {response.status_code}")
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
                    # Skip forks, archived, disabled, and empty repos
                    if repo.get("fork") or repo.get("archived"):
                        continue
                    
                    # Skip disabled repos
                    if repo.get("disabled", False):
                        continue
                    
                    # Skip empty repos (size = 0 usually means no commits)
                    repo_size = repo.get("size", 0)
                    if repo_size == 0:
                        continue

                    user_repos.append({
                        "name_with_owner": repo["full_name"],
                        "name": repo["name"],
                        "description": repo.get("description"),
                        "url": repo["html_url"],
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "watchers": repo.get("subscribers_count", repo["watchers_count"]),  # Use subscribers_count (true watchers), fallback to watchers_count
                        "language": repo.get("language"),
                        "topics": repo.get("topics", []),  # Topics are already in the response
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

            # Validate user meets criteria: repos >= 10 OR (repos 1-9 AND followers >= 5)
            if not user_fetch_failed:
                non_fork_repos_count = len(user_repos)

                # If user has < 10 non-fork repos, check followers requirement
                if non_fork_repos_count < 10:
                    # Get user info to check followers
                    try:
                        user_url = f"https://api.github.com/users/{username}"
                        user_response = requests.get(user_url, headers=headers, timeout=10)

                        if user_response.status_code == 200:
                            user_info = user_response.json()
                            followers_count = user_info.get("followers", 0)

                            # Criteria: 1-9 repos need followers >= 5
                            if non_fork_repos_count > 0 and followers_count < 5:
                                print(f"   [SKIP]  Filtered {username}: {non_fork_repos_count} repos but only {followers_count} followers (need >= 5)", flush=True)
                                filtered += 1
                                failure_reasons["filtered_criteria"] += 1
                                continue
                            if non_fork_repos_count == 0:
                                # No valid repos at all (all were forks/archived)
                                print(f"   [SKIP]  Filtered {username}: no non-fork repos (followers: {followers_count})", flush=True)
                                filtered += 1
                                failure_reasons["filtered_criteria"] += 1
                                continue
                        else:
                            # Can't verify followers, but already have repos, so accept
                            if non_fork_repos_count > 0:
                                print(f"   [WARNING]  Couldn't verify followers for {username}, accepting anyway ({non_fork_repos_count} repos)", flush=True)
                            else:
                                # No repos and can't verify
                                print(f"   [SKIP]  Filtered {username}: no repos and couldn't verify followers", flush=True)
                                filtered += 1
                                failure_reasons["filtered_criteria"] += 1
                                continue
                    except Exception as e:
                        if non_fork_repos_count > 0:
                            print(f"   [WARNING]  Error checking followers for {username}: {e}, accepting anyway ({non_fork_repos_count} repos)", flush=True)
                        else:
                            print(f"   [SKIP]  Filtered {username}: no repos and error checking followers: {e}", flush=True)
                            filtered += 1
                            failure_reasons["filtered_criteria"] += 1
                            continue

                # User meets criteria
                all_repos.extend(user_repos)
                successful += 1
                print(f"   [OK] Got {len(user_repos)} repos from {username}", flush=True)

        except Exception as e:
            print("[ERROR] Exception fetching repos for {username}: {type(e).__name__}: {e}")
            failed += 1
            failure_reasons["exception"] += 1
            continue

    # Print summary for this batch
    if failed > 0 or filtered > 0:
        print("\n[STATS] Batch Summary:")
        print("   Checked: {checked}, Successful: {successful}, Filtered: {filtered}, Failed: {failed}")
        if failed > 0:
            print("   Failed (errors):")
            print("      User not found/inaccessible: {failure_reasons['user_not_found']}")
            print("      Rate limit hits: {failure_reasons['rate_limit']}")
            print("      API errors: {failure_reasons['api_error']}")
            print("      Exceptions: {failure_reasons['exception']}")
        if filtered > 0:
            print("   Filtered (doesn't meet criteria): {failure_reasons['filtered_criteria']}")

    return {
        "batch_size": len(usernames),
        "checked_users": checked,
        "successful_users": successful,
        "failed_users": failed,
        "filtered_users": filtered,
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

    print(f"[SEARCH] Searching for Seattle developers (target: {max_users})...")

    while len(usernames) < max_users:
        url = f"https://api.github.com/search/users"
        params = {
            "q": "location:seattle",
            "per_page": per_page,
            "page": page,
            "sort": "repositories",
            "order": "desc"
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code != 200:
            print("[ERROR] Error searching users: {response.status_code}")
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

    print("[OK] Found {len(usernames)} Seattle developers")
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

    print("[START] Starting distributed collection")
    print("   Target: {target_projects} projects")
    print("   Max users: {max_users}")
    print("   Batch size: {batch_size} users/batch")

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

    print("[PKG] Split {len(usernames)} users into {len(user_batches)} batches")

    # Step 3: Distribute batches to workers (parallel)
    job = group(fetch_users_batch_task.s(batch) for batch in user_batches)
    result = job.apply_async()

    print("⚡ Spawned {len(user_batches)} parallel tasks")
    print("   Waiting for workers to complete...")

    # Step 4: Wait and aggregate results
    batch_results = result.get(timeout=None)  # No timeout - wait until all tasks complete

    all_projects = []
    for batch_result in batch_results:
        all_projects.extend(batch_result["repos"])

    # Step 5: Sort by stars and limit
    all_projects.sort(key=lambda x: x["stars"], reverse=True)
    all_projects = all_projects[:target_projects]

    total_stars = sum(p["stars"] for p in all_projects)

    print("\n[OK] Collection complete!")
    print("   Total projects: {len(all_projects)}")
    print("   Total stars: {total_stars:,}")

    return {
        "success": True,
        "total_projects": len(all_projects),
        "total_stars": total_stars,
        "total_users": len(usernames),
        "total_batches": len(user_batches),
        "projects": all_projects,
        "completed_at": datetime.utcnow().isoformat()
    }


@celery_app.task(bind=True, max_retries=3, name="workers.collection_worker.update_watchers_batch")
def update_watchers_batch_task(self, repos_batch):
    """
    Celery task to update watchers for a batch of repos.
    Uses GraphQL for batch query, then REST API only for suspicious repos.

    Args:
        repos_batch: List of dicts with 'owner' and 'name' keys

    Returns:
        Dict with results: {repo_key: watchers_count or None if deleted/empty}
    """
    import requests
    from utils.token_manager import TokenManager
    import time

    token_manager = TokenManager()
    token = token_manager.get_token()

    # Step 1: Build GraphQL batch query for all repos
    aliases = []
    repo_keys = []

    for idx, repo in enumerate(repos_batch):
        owner = repo['owner']['login'] if isinstance(repo['owner'], dict) else repo['owner']
        repo_name = repo['name']
        repo_keys.append(f"{owner}/{repo_name}")
        safe_alias = f"repo_{idx}"

        aliases.append(f'''
    {safe_alias}: repository(owner: "{owner}", name: "{repo_name}") {{
        isEmpty
        isLocked
        isArchived
        watchers {{
            totalCount
        }}
    }}''')

    query = "{" + "".join(aliases) + "\n}"

    headers_graphql = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json',
    }

    results = {}

    try:
        # Execute GraphQL query
        response = requests.post(
            'https://api.github.com/graphql',
            headers=headers_graphql,
            json={'query': query},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            if 'data' in data:
                for idx, repo_key in enumerate(repo_keys):
                    safe_alias = f"repo_{idx}"
                    repo_data = data['data'].get(safe_alias)

                    if repo_data:
                        # Check if repo should be filtered
                        if repo_data.get('isEmpty') or repo_data.get('isLocked') or repo_data.get('isArchived'):
                            # Mark for deletion
                            results[repo_key] = None
                        elif repo_data.get('watchers'):
                            results[repo_key] = repo_data['watchers']['totalCount']
                        else:
                            # Repo exists but no watchers data
                            results[repo_key] = None
                    else:
                        # Repo deleted or inaccessible
                        results[repo_key] = None

            else:
                # GraphQL error - mark all as needing retry
                print(f"[ERROR] GraphQL error in batch: {data.get('errors', 'Unknown')}")
                for repo_key in repo_keys:
                    results[repo_key] = None
        else:
            # HTTP error - mark all as needing retry
            print(f"[ERROR] HTTP {response.status_code} in batch")
            for repo_key in repo_keys:
                results[repo_key] = None

        return results

    except requests.exceptions.Timeout:
        print(f"[ERROR] Timeout in batch of {len(repos_batch)} repos")
        # Mark all as None to trigger retry or manual check
        return {repo_key: None for repo_key in repo_keys}
    except Exception as e:
        print(f"[ERROR] Exception in batch: {type(e).__name__}: {e}")
        if self.request.retries < 1:
            raise self.retry(exc=e, countdown=10)
        else:
            # Final failure - mark all as None
            return {repo_key: None for repo_key in repo_keys}
