import json
from typing import List, Dict

class InfluenceAnalyzer:
    """
    Calculate the influence score for each user or repository.
    Formula:
        influence = w1*stars + w2*forks + w3*watchers
        final_score = influence * verified_prob
    """
    def __init__(self, weights=None):
        # Weights can be adjusted based on requirements
        self.weights = weights or {"stars": 0.4, "forks": 0.3, "watchers": 0.3}

    def compute_influence(self, repo: Dict) -> float:
        """Calculate base influence score based on repository metrics"""
        stars = repo.get("stars", 0)
        forks = repo.get("forks", 0)
        watchers = repo.get("watchers", 0)
        w = self.weights
        return (w["stars"] * stars) + (w["forks"] * forks) + (w["watchers"] * watchers)

    def combine_with_verification(self, repos: List[Dict], verified_prob: float = 0.8) -> List[Dict]:
        """Integrate geographic credibility to generate final scores"""
        results = []
        for r in repos:
            base_score = self.compute_influence(r)
            final_score = base_score * verified_prob
            r["influence_score"] = round(base_score, 2)
            r["verified_prob"] = verified_prob
            r["final_score"] = round(final_score, 2)
            results.append(r)
        return results

    def save_results(self, results: List[Dict], filename="data/results_seattle.json"):
        """Save results as JSON"""
        import os
        os.makedirs("data", exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"✅ Results saved to {filename}")

    def print_table(self, results: List[Dict], top_n: int = 10):
        """Simple CLI table output"""
        print("\n--------------------------------------------")
        print(f"{'Repo':25s} {'Stars':>6s} {'Forks':>6s} {'Influence':>10s} {'Final':>8s}")
        print("--------------------------------------------")
        for r in sorted(results, key=lambda x: x["final_score"], reverse=True)[:top_n]:
            name = r["name"][:24]
            print(f"{name:25s} {r['stars']:6d} {r['forks']:6d} {r['influence_score']:10.1f} {r['final_score']:8.1f}")
        print("--------------------------------------------")
