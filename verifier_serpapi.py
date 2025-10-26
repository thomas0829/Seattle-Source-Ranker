import os
import requests
import re
from typing import Dict, List

class SerpAPIVerifier:
    def __init__(self, verbose: bool = True):
        self.api_key = os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise ValueError("❌ Missing SERPAPI_KEY environment variable.")
        self.verbose = verbose
        self.endpoint = "https://serpapi.com/search"
        self.keywords = [
            r"seattle", r"redmond", r"bellevue", r"kirkland", r"tacoma", r"washington(,|\s|$)"
        ]

    def verify_user(self, username: str) -> Dict:
        """Search LinkedIn or websites for Seattle location keywords"""
        query = f'site:linkedin.com/in "{username}" Seattle OR Redmond OR Bellevue'
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "num": 5
        }

        try:
            res = requests.get(self.endpoint, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            if self.verbose:
                print(f"[{username}] ❌ SerpAPI error: {e}")
            return {"username": username, "verified": False, "source": "error", "confidence": 0.0}

        verified, confidence = False, 0.0
        for item in data.get("organic_results", []):
            snippet = (item.get("snippet") or "").lower()
            title = (item.get("title") or "").lower()
            if any(re.search(kw, snippet) or re.search(kw, title) for kw in self.keywords):
                verified, confidence = True, 0.9
                break
        if not verified:
            confidence = 0.3

        if self.verbose:
            print(f"[{username}] verified={verified}, confidence={confidence:.2f}")

        return {
            "username": username,
            "verified": verified,
            "source": "serpapi",
            "confidence": confidence
        }

    def verify_batch(self, users: List[Dict]) -> List[Dict]:
        results = []
        for user in users:
            username = user.get("login", "")
            result = self.verify_user(username)
            results.append(result)
        return results
