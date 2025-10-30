"""
GitHub GraphQL Client for industrial-grade data collection
Supports cursor-based pagination, checkpoint recovery, and batch fetching
"""
import os
import json
import time
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from tqdm import tqdm


class GitHubGraphQLClient:
    """
    Industrial-grade GitHub GraphQL client with cursor pagination support.
    Breaks through the REST API 1000 result limit.
    """
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("❌ GitHub token not found. Set GITHUB_TOKEN environment variable.")
        
        self.endpoint = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.rate_limit_remaining = 5000
        self.rate_limit_reset_at = None
        
    def _execute_query(self, query: str, variables: Dict[str, Any]) -> Dict:
        """
        Execute a GraphQL query with error handling and rate limit tracking.
        """
        payload = {
            "query": query,
            "variables": variables
        }
        
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Track rate limit
            if "data" in result and "rateLimit" in result["data"]:
                rate_limit = result["data"]["rateLimit"]
                self.rate_limit_remaining = rate_limit.get("remaining", 0)
                self.rate_limit_reset_at = rate_limit.get("resetAt")
                
                # Auto-throttle if running low
                if self.rate_limit_remaining < 100:
                    print(f"⚠️  Low rate limit: {self.rate_limit_remaining} remaining. Throttling...")
                    time.sleep(2)
            
            # Check for errors
            if "errors" in result:
                print(f"❌ GraphQL errors: {result['errors']}")
                return None
                
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def search_repositories(
        self,
        query: str,
        cursor: Optional[str] = None,
        batch_size: int = 100
    ) -> Optional[Dict]:
        """
        Search repositories with cursor-based pagination.
        
        Args:
            query: GitHub search query (e.g., "location:seattle stars:>100")
            cursor: Cursor for pagination (None for first page)
            batch_size: Number of results per page (max 100)
            
        Returns:
            Dict containing repositories and pagination info
        """
        
        graphql_query = """
        query SearchRepositories($searchQuery: String!, $cursor: String, $first: Int!) {
          rateLimit {
            remaining
            resetAt
          }
          search(query: $searchQuery, type: REPOSITORY, first: $first, after: $cursor) {
            repositoryCount
            pageInfo {
              endCursor
              hasNextPage
            }
            edges {
              node {
                ... on Repository {
                  nameWithOwner
                  name
                  description
                  url
                  stargazerCount
                  forkCount
                  watchers {
                    totalCount
                  }
                  issues(states: OPEN) {
                    totalCount
                  }
                  createdAt
                  updatedAt
                  pushedAt
                  primaryLanguage {
                    name
                  }
                  owner {
                    login
                    ... on User {
                      name
                      location
                      company
                      bio
                    }
                    ... on Organization {
                      name
                      location
                      description
                    }
                  }
                  licenseInfo {
                    name
                    spdxId
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {
            "searchQuery": query,
            "cursor": cursor,
            "first": min(batch_size, 100)  # Max 100 per request
        }
        
        result = self._execute_query(graphql_query, variables)
        
        if not result or "data" not in result:
            return None
            
        return result["data"]["search"]
    
    def fetch_all_repositories(
        self,
        query: str,
        max_results: Optional[int] = None,
        checkpoint_callback=None,
        progress_bar: bool = True
    ) -> List[Dict]:
        """
        Fetch all repositories matching the query using cursor pagination.
        Supports checkpoint recovery for long-running operations.
        
        Args:
            query: GitHub search query
            max_results: Maximum number of results to fetch (None = all)
            checkpoint_callback: Callback function(cursor, count) for saving progress
            progress_bar: Show progress bar
            
        Returns:
            List of repository dictionaries
        """
        
        all_repos = []
        cursor = None
        total_fetched = 0
        
        # Get total count first
        initial_result = self.search_repositories(query, cursor=None, batch_size=1)
        if not initial_result:
            print("❌ Failed to fetch initial result")
            return []
        
        total_count = initial_result["repositoryCount"]
        if max_results:
            total_count = min(total_count, max_results)
        
        print(f"📊 Total repositories found: {initial_result['repositoryCount']}")
        print(f"🎯 Will fetch: {total_count}")
        
        pbar = tqdm(total=total_count, desc="Fetching repos") if progress_bar else None
        
        while True:
            # Fetch batch
            result = self.search_repositories(query, cursor=cursor, batch_size=100)
            
            if not result:
                print("❌ Failed to fetch batch, stopping")
                break
            
            # Extract repositories
            repos = []
            for edge in result.get("edges", []):
                node = edge.get("node", {})
                if node:
                    # Flatten the structure for easier use
                    repo = {
                        "name_with_owner": node.get("nameWithOwner"),
                        "name": node.get("name"),
                        "description": node.get("description"),
                        "url": node.get("url"),
                        "stars": node.get("stargazerCount", 0),
                        "forks": node.get("forkCount", 0),
                        "watchers": node.get("watchers", {}).get("totalCount", 0),
                        "open_issues": node.get("issues", {}).get("totalCount", 0),
                        "created_at": node.get("createdAt"),
                        "updated_at": node.get("updatedAt"),
                        "pushed_at": node.get("pushedAt"),
                        "language": node.get("primaryLanguage", {}).get("name") if node.get("primaryLanguage") else None,
                        "languages": [
                            {"name": edge["node"]["name"], "size": edge["size"]}
                            for edge in node.get("languages", {}).get("edges", [])
                        ],
                        "license": node.get("licenseInfo", {}).get("name") if node.get("licenseInfo") else None,
                        "topics": [
                            edge["node"]["topic"]["name"]
                            for edge in node.get("repositoryTopics", {}).get("edges", [])
                        ],
                        "owner": {
                            "login": node.get("owner", {}).get("login"),
                            "name": node.get("owner", {}).get("name"),
                            "location": node.get("owner", {}).get("location"),
                            "company": node.get("owner", {}).get("company"),
                        },
                        "release_count": node.get("releases", {}).get("totalCount", 0),
                        "latest_release": node.get("releases", {}).get("nodes", [{}])[0].get("tagName") if node.get("releases", {}).get("nodes") else None,
                    }
                    repos.append(repo)
            
            all_repos.extend(repos)
            total_fetched += len(repos)
            
            if pbar:
                pbar.update(len(repos))
            
            # Checkpoint callback
            page_info = result.get("pageInfo", {})
            cursor = page_info.get("endCursor")
            
            if checkpoint_callback and cursor:
                checkpoint_callback(cursor, total_fetched)
            
            # Check stopping conditions
            if not page_info.get("hasNextPage"):
                print("✅ Reached end of results")
                break
                
            if max_results and total_fetched >= max_results:
                print(f"✅ Reached max results limit: {max_results}")
                break
            
            # Rate limiting courtesy delay
            time.sleep(0.5)
        
        if pbar:
            pbar.close()
        
        print(f"✅ Total fetched: {len(all_repos)} repositories")
        return all_repos
    
    def get_repository_details(self, owner: str, name: str) -> Optional[Dict]:
        """
        Get detailed information for a specific repository.
        """
        query = """
        query GetRepository($owner: String!, $name: String!) {
          rateLimit {
            remaining
            resetAt
          }
          repository(owner: $owner, name: $name) {
            nameWithOwner
            description
            url
            stargazerCount
            forkCount
            watchers {
              totalCount
            }
            issues(states: OPEN) {
              totalCount
            }
            pullRequests(states: OPEN) {
              totalCount
            }
            createdAt
            updatedAt
            pushedAt
            primaryLanguage {
              name
            }
            diskUsage
            owner {
              login
              ... on User {
                name
                location
                company
              }
            }
          }
        }
        """
        
        variables = {"owner": owner, "name": name}
        result = self._execute_query(query, variables)
        
        if result and "data" in result:
            return result["data"].get("repository")
        return None


def main():
    """Demo usage"""
    client = GitHubGraphQLClient()
    
    # Example: Search for Seattle repositories
    query = "location:seattle stars:>100"
    
    print("🚀 Starting GraphQL-based repository fetch...")
    print(f"📝 Query: {query}\n")
    
    repos = client.fetch_all_repositories(
        query=query,
        max_results=500,  # Limit for demo
        progress_bar=True
    )
    
    # Save results
    output_file = "data/graphql_repos.json"
    os.makedirs("data", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(repos, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved {len(repos)} repositories to {output_file}")
    
    # Show sample
    if repos:
        print("\n📊 Sample repository:")
        sample = repos[0]
        print(f"  Name: {sample['name_with_owner']}")
        print(f"  Stars: {sample['stars']}")
        print(f"  Language: {sample['language']}")
        print(f"  Owner Location: {sample['owner']['location']}")


if __name__ == "__main__":
    main()
