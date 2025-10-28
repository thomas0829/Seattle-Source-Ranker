#!/usr/bin/env python3
"""
Update existing ranked data with PyPI download statistics
"""
import json
from pypi_client import PyPIClient
from tqdm import tqdm
import math

def main():
    input_file = "data/ranked_by_language_seattle.json"
    output_file = "data/ranked_by_language_seattle.json"
    
    print("📥 Loading existing data...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    python_repos = data.get("Python", [])
    
    if not python_repos:
        print("❌ No Python repositories found")
        return
    
    print(f"📦 Fetching PyPI data for {len(python_repos)} Python repositories...")
    client = PyPIClient()
    
    # Fetch PyPI data
    for repo in tqdm(python_repos, desc="PyPI lookup"):
        pypi_info = client.get_package_info(repo["name"])
        repo["pypi_package"] = pypi_info["package_name"]
        repo["pypi_exists"] = pypi_info["exists"]
        repo["pypi_downloads_month"] = pypi_info["downloads_month"]
    
    # Count successful fetches
    with_pypi = sum(1 for r in python_repos if r.get("pypi_exists", False))
    print(f"✅ Found PyPI data for {with_pypi}/{len(python_repos)} packages")
    
    # Recalculate scores
    max_downloads = max((r.get("pypi_downloads_month", 0) for r in python_repos), default=1)
    print(f"\n🔢 Recalculating scores...")
    print(f"   Max downloads/month: {max_downloads:,}")
    
    for repo in python_repos:
        downloads = repo.get("pypi_downloads_month", 0)
        github_score = repo.get("score", 0)
        
        if downloads > 0:
            # 40% GitHub + 60% PyPI (log normalized)
            pypi_score = math.log10(downloads + 1) / math.log10(max_downloads + 1)
            repo["pypi_score"] = round(pypi_score, 4)
            repo["final_score"] = round(0.4 * github_score + 0.6 * pypi_score, 4)
            repo["score_type"] = "github+pypi"
        else:
            repo["final_score"] = github_score
            repo["score_type"] = "github_only"
    
    # Sort by final score
    python_repos.sort(key=lambda x: x.get("final_score", x.get("score", 0)), reverse=True)
    
    # Update other languages with final_score
    for lang in ["C++", "Other"]:
        for repo in data.get(lang, []):
            if "final_score" not in repo:
                repo["final_score"] = repo.get("score", 0)
                repo["score_type"] = "github_only"
    
    # Update metadata
    if "metadata" not in data:
        data["metadata"] = {}
    data["metadata"]["pypi_integrated"] = True
    data["metadata"]["python_with_pypi"] = with_pypi
    
    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n💾 Updated data saved to {output_file}")
    
    # Show top 10 with PyPI data
    print(f"\n🏆 Top 10 Python Projects (with PyPI integration):")
    print("=" * 95)
    print(f"{'Repo':35s} {'Stars':>8s} {'Downloads/mo':>15s} {'GitHub':>8s} {'Final':>8s} {'Type':>10s}")
    print("=" * 95)
    
    for repo in python_repos[:10]:
        name = repo["name"][:33]
        stars = repo.get("stars", 0)
        downloads = repo.get("pypi_downloads_month", 0)
        github_score = repo.get("score", 0)
        final_score = repo.get("final_score", github_score)
        score_type = repo.get("score_type", "github")[:9]
        
        downloads_str = f"{downloads:,}"[:13] if downloads > 0 else "N/A"
        print(f"{name:35s} {stars:8,d} {downloads_str:>15s} {github_score:8.4f} {final_score:8.4f} {score_type:>10s}")

if __name__ == "__main__":
    main()
