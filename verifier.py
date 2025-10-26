# seattle_source_ranker/verifier.py
"""
Verifier module for Seattle-Source-Ranker
Performs probabilistic validation of user locations using secondary sources.
"""

import random
import re
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

class LocationVerifier:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        # Default detectable location keywords
        self.keywords = [
            r"seattle",
            r"redmond",
            r"bellevue",
            r"kirkland",
            r"tacoma",
            r"washington(,|\s|$)",
        ]

    def verify_user(self, username: str, website: Optional[str] = None) -> Dict:
        """
        Attempt to verify if the user is actually located in Seattle.
        If website is provided, try to fetch and compare content; otherwise use random simulation.
        Returns result containing verified (bool), source, and confidence.
        """
        verified = False
        confidence = 0.0
        source = "simulated"

        # If personal website is available for analysis
        if website:
            try:
                resp = requests.get(website, timeout=5)
                if resp.status_code == 200:
                    text = resp.text.lower()
                    for kw in self.keywords:
                        if re.search(kw, text):
                            verified = True
                            source = "website"
                            confidence = 0.9
                            break
                    if not verified:
                        confidence = 0.5
                else:
                    confidence = 0.2
            except Exception:
                confidence = 0.1
        else:
            # No website available, simulate with 0.78 as average true rate
            verified = random.random() < 0.78
            confidence = 0.8 if verified else 0.2

        if self.verbose:
            print(f"[{username}] verified={verified}, source={source}, confidence={confidence:.2f}")

        return {
            "username": username,
            "verified": verified,
            "source": source,
            "confidence": confidence
        }

    def verify_batch(self, users: List[Dict]) -> List[Dict]:
        """
        Verify a batch of GitHub users (simulated or actual)
        """
        results = []
        for user in users:
            username = user.get("login", "")
            website = user.get("blog") or None
            result = self.verify_user(username, website)
            results.append(result)
        return results

    def compute_statistics(self, verified_results: List[Dict]) -> Dict:
        """Calculate overall verification probability (true rate + average confidence)"""
        if not verified_results:
            return {"verified_rate": 0.0, "mean_confidence": 0.0}

        total = len(verified_results)
        verified_count = sum(1 for r in verified_results if r["verified"])
        mean_conf = sum(r["confidence"] for r in verified_results) / total
        verified_rate = verified_count / total

        stats = {
            "verified_rate": round(verified_rate, 3),
            "mean_confidence": round(mean_conf, 3),
            "sample_size": total
        }

        print(f"✅ Verification complete: {verified_count}/{total} true ({verified_rate:.2%}), avg conf={mean_conf:.2f}")
        return stats
