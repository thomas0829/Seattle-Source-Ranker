# seattle_source_ranker/github_client.py
import os
import requests
from typing import List, Dict

GITHUB_API_URL = "https://api.github.com"

class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("❌ GitHub token not found. Please set GITHUB_TOKEN environment variable.")
        self.headers = {"Authorization": f"token {self.token}"}

    def search_users(self, location: str, per_page: int = 30, page: int = 1) -> List[Dict]:
        """Search GitHub users by location keyword."""
        q = f"location:{location}"
        url = f"{GITHUB_API_URL}/search/users?q={q}&per_page={per_page}&page={page}"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        return res.json().get("items", [])

    def get_user_repos(self, username: str) -> List[Dict]:
        """Get public repositories of a given user."""
        url = f"{GITHUB_API_URL}/users/{username}/repos"
        res = requests.get(url, headers=self.headers)
        if res.status_code == 404:
            return []
        res.raise_for_status()
        return res.json()

    def get_repo_metrics(self, owner: str, repo: str) -> Dict:
        """Get stars, forks, and watchers for a repository."""
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        data = res.json()
        return {
            "name": data["full_name"],
            "stars": data["stargazers_count"],
            "forks": data["forks_count"],
            "watchers": data["watchers_count"],
            "open_issues": data["open_issues_count"],
        }
