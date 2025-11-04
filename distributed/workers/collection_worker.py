"""
Distributed collection worker using Celery
Each worker fetches repositories for a batch of users in parallel
"""
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from celery import Task

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.celery_config import celery_app
from collectors.graphql_client import GitHubGraphQLClient


class CollectionTask(Task):
    """Base task with shared GraphQL client"""
    _graphql_client = None
    
    @property
    def graphql_client(self):
        if self._graphql_client is None:
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                raise ValueError("❌ GITHUB_TOKEN not found in worker environment")
            self._graphql_client = GitHubGraphQLClient(token=token)
        return self._graphql_client


@celery_app.task(
    bind=True,
    base=CollectionTask,
    name="workers.collection_worker.fetch_user_repos",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def fetch_user_repos_task(self, username: str) -> Dict[str, Any]:
    """
    Fetch all repositories for a single user using GraphQL
    
    Args:
        username: GitHub username
        
    Returns:
        Dict with user info and their repositories
    """
    try:
        client = self.graphql_client
        
        # GraphQL query to fetch user/org repos
        # Use repositoryOwner to support both users and organizations
        query = """
        query($username: String!, $cursor: String) {
          repositoryOwner(login: $username) {
            login
            ... on User {
              name
              location
              company
              email
              bio
            }
            ... on Organization {
              name
              location
              description
            }
            repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, orderBy: {field: STARGAZERS, direction: DESC}) {
              totalCount
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                nameWithOwner
                name
                description
                url
                stargazerCount
                forkCount
                watchers { totalCount }
                primaryLanguage { name }
                createdAt
                updatedAt
                pushedAt
                isArchived
                isFork
                openIssues: issues(states: OPEN) { totalCount }
                hasIssuesEnabled
              }
            }
          }
        }
        """
        
        all_repos = []
        cursor = None
        has_next_page = True
        
        while has_next_page:
            variables = {"username": username}
            if cursor:
                variables["cursor"] = cursor
            
            result = client._execute_query(query, variables)
            
            if not result or "data" not in result:
                return {
                    "username": username,
                    "success": False,
                    "error": "Query execution failed",
                    "repos": []
                }
            
            if "repositoryOwner" not in result["data"] or not result["data"]["repositoryOwner"]:
                return {
                    "username": username,
                    "success": False,
                    "error": "User/Organization not found",
                    "repos": []
                }
            
            user_data = result["data"]["repositoryOwner"]
            repos_data = user_data["repositories"]
            
            # Extract repos
            for repo in repos_data["nodes"]:
                if not repo["isFork"] and not repo["isArchived"]:
                    all_repos.append({
                        "name_with_owner": repo["nameWithOwner"],
                        "name": repo["name"],
                        "description": repo.get("description"),
                        "url": repo["url"],
                        "stars": repo["stargazerCount"],
                        "forks": repo["forkCount"],
                        "watchers": repo["watchers"]["totalCount"],
                        "language": repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else None,
                        "created_at": repo["createdAt"],
                        "updated_at": repo["updatedAt"],
                        "pushed_at": repo["pushedAt"],
                        "open_issues": repo["openIssues"]["totalCount"],
                        "has_issues": repo["hasIssuesEnabled"],
                        "owner": {
                            "login": user_data["login"],
                            "name": user_data.get("name"),
                            "location": user_data.get("location"),
                            "company": user_data.get("company"),
                            "email": user_data.get("email"),
                            "bio": user_data.get("bio"),
                        }
                    })
            
            # Pagination
            page_info = repos_data["pageInfo"]
            has_next_page = page_info["hasNextPage"]
            cursor = page_info["endCursor"]
        
        return {
            "username": username,
            "success": True,
            "total_repos": len(all_repos),
            "repos": all_repos,
            "fetched_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        # Retry on failure
        self.retry(exc=e, countdown=60)


@celery_app.task(
    bind=True,
    name="workers.collection_worker.fetch_users_batch",
    max_retries=3,
)
def fetch_users_batch_task(self, usernames: List[str]) -> Dict[str, Any]:
    """
    Fetch repos for a batch of users
    Processes each user sequentially within this task
    
    Args:
        usernames: List of GitHub usernames
        
    Returns:
        Dict with aggregated results
    """
    all_repos = []
    successful = 0
    failed = 0
    
    # Process each user in this batch sequentially
    for username in usernames:
        try:
            # Call the fetch function directly (not as a task)
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                print(f"❌ GITHUB_TOKEN not found in worker environment!")
                failed += 1
                continue
            client = GitHubGraphQLClient(token=token)
            
            # GraphQL query to fetch user/org repos
            # Use repositoryOwner to support both users and organizations
            query = """
            query($username: String!, $cursor: String) {
              repositoryOwner(login: $username) {
                login
                ... on User {
                  name
                  location
                  company
                  email
                  bio
                }
                ... on Organization {
                  name
                  location
                  description
                }
                repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, orderBy: {field: STARGAZERS, direction: DESC}) {
                  totalCount
                  pageInfo {
                    hasNextPage
                    endCursor
                  }
                  nodes {
                    nameWithOwner
                    name
                    description
                    url
                    stargazerCount
                    forkCount
                    watchers { totalCount }
                    primaryLanguage { name }
                    createdAt
                    updatedAt
                    pushedAt
                    isArchived
                    isFork
                    openIssues: issues(states: OPEN) { totalCount }
                    hasIssuesEnabled
                  }
                }
              }
            }
            """
            
            user_repos = []
            cursor = None
            has_next_page = True
            user_fetch_failed = False
            
            while has_next_page:
                variables = {"username": username}
                if cursor:
                    variables["cursor"] = cursor
                
                result = client._execute_query(query, variables)
                
                if not result or "data" not in result:
                    failed += 1
                    user_fetch_failed = True
                    break
                
                if "repositoryOwner" not in result["data"] or not result["data"]["repositoryOwner"]:
                    failed += 1
                    user_fetch_failed = True
                    break
                
                user_data = result["data"]["repositoryOwner"]
                repos_data = user_data["repositories"]
                
                # Extract repos
                for repo in repos_data["nodes"]:
                    if not repo["isFork"] and not repo["isArchived"]:
                        user_repos.append({
                            "name_with_owner": repo["nameWithOwner"],
                            "name": repo["name"],
                            "description": repo.get("description"),
                            "url": repo["url"],
                            "stars": repo["stargazerCount"],
                            "forks": repo["forkCount"],
                            "watchers": repo["watchers"]["totalCount"],
                            "language": repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else None,
                            "created_at": repo["createdAt"],
                            "updated_at": repo["updatedAt"],
                            "pushed_at": repo["pushedAt"],
                            "open_issues": repo["openIssues"]["totalCount"],
                            "has_issues": repo["hasIssuesEnabled"],
                            "owner": {
                                "login": user_data["login"],
                                "name": user_data.get("name"),
                                "location": user_data.get("location"),
                                "company": user_data.get("company"),
                                "email": user_data.get("email"),
                                "bio": user_data.get("bio"),
                            }
                        })
                
                # Pagination
                page_info = repos_data["pageInfo"]
                has_next_page = page_info["hasNextPage"]
                cursor = page_info["endCursor"]
            
            # Only mark as successful if we didn't fail during fetching
            if not user_fetch_failed:
                all_repos.extend(user_repos)
                successful += 1
            
        except Exception as e:
            print(f"Error fetching repos for {username}: {e}")
            failed += 1
            continue
    
    return {
        "batch_size": len(usernames),
        "successful_users": successful,
        "failed_users": failed,
        "total_repos": len(all_repos),
        "repos": all_repos,
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
