import argparse
import os
import json
import requests
from datetime import datetime, timezone
from tqdm import tqdm  # Progress bar for better UX
from github_client import GitHubClient

try:
    from pypi_client import PyPIClient
    PYPI_AVAILABLE = True
except ImportError:
    PYPI_AVAILABLE = False
    print("⚠️ PyPI client not available. Install 'requests' to enable PyPI integration.")

"""
===========================================================
 Seattle-Source-Ranker (Project-based Localization Model)
===========================================================

【Objective】
From GitHub's popular repositories,
identify projects where the owner.location is in the Seattle area,
and calculate influence scores based on multi-dimensional metrics.

-----------------------------------------------------------
【Influence Formula】
Score = 0.4 * S_norm + 0.25 * F_norm + 0.15 * W_norm + 0.10 * T_age + 0.10 * H_health

Component Explanation:
- S_norm: Normalized stars (community popularity)
- F_norm: Normalized forks (community engagement)
- W_norm: Normalized watchers (long-term attention)
- T_age: Project age weight (older projects score higher)
         T_age = years / (years + 2)
- H_health: Health score (fewer open issues = higher score)
         H_health = 1 - (issues / (issues + 10))
===========================================================
"""

# -------------------------- Utility Functions --------------------------
def normalize(value, max_value):
    return value / max_value if max_value > 0 else 0

def age_weight(created_at):
    """Calculate age weight based on project creation time (older = higher score)."""
    try:
        created_time = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        years = (datetime.now(timezone.utc) - created_time).days / 365
        return years / (years + 2) if years > 0 else 0.3
    except Exception:
        return 0.3

def health_score(issues):
    """Calculate health score based on open issues count (fewer = better)."""
    return 1 - (issues / (issues + 10))

def save_json(data, filename):
    """Save a dictionary or list as JSON."""
    os.makedirs("data", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"💾 Saved to {filename}")

# -------------------------- Main --------------------------
def main():
    parser = argparse.ArgumentParser(description="Seattle-Source-Ranker (with PyPI integration)")
    parser.add_argument("--location", type=str, default="Seattle", help="Developer location keyword (e.g. Seattle)")
    parser.add_argument("--topk", type=int, default=50, help="Number of Seattle-based repos to collect")
    parser.add_argument("--max-pages", type=int, default=20, help="Max number of pages to fetch (safety cap)")
    parser.add_argument("--fetch-pypi", action="store_true", help="Fetch PyPI download stats for Python projects")
    args = parser.parse_args()

    client = GitHubClient()
    headers = {"Authorization": f"token {client.token}"}
    per_page = 100
    location_keywords = ["seattle", "redmond", "bellevue", "kirkland", "washington"]

    print(f"🚀 Searching GitHub for repositories by developers in {args.location}...\n")
    localized_repos = []
    owner_cache = {}
    cache_file = "data/owner_location_cache.json"

    # 📦 Load cache if it exists
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                owner_cache = json.load(f)
            print(f"📦 Loaded {len(owner_cache)} cached owner locations\n")
        except Exception:
            owner_cache = {}

    # 🚀 Fetch repositories page by page with progress bar
    page = 1
    pbar = tqdm(total=args.topk, desc="Collecting Seattle-area repositories", ncols=80)

    while len(localized_repos) < args.topk and page <= args.max_pages:
        url = f"https://api.github.com/search/repositories?q=stars:>10&sort=stars&order=desc&per_page={per_page}&page={page}"
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            pbar.close()
            print(f"\n⚠️ API Error {res.status_code}: {res.text}")
            break

        repos = res.json().get("items", [])
        if not repos:
            pbar.close()
            print("\n❌ No more repositories found.")
            break

        for repo in repos:
            owner_login = repo["owner"]["login"]

            # ✅ Use cached data if available
            if owner_login in owner_cache:
                location = owner_cache[owner_login]
            else:
                owner_url = repo["owner"]["url"]
                try:
                    owner_data = requests.get(owner_url, headers=headers).json()
                    location = (owner_data.get("location") or "").lower()
                    owner_cache[owner_login] = location
                except Exception:
                    continue

            if any(loc in location for loc in location_keywords):
                localized_repos.append(repo)
                pbar.update(1)  # ✅ Update progress bar

            if len(localized_repos) >= args.topk:
                pbar.n = args.topk
                pbar.last_print_n = args.topk
                pbar.refresh()
                pbar.close()
                print(f"\n🎯 Reached target of {args.topk} repositories, stopping early.")
                break

        if len(localized_repos) >= args.topk:
            break

        page += 1

    if not pbar.disable:
        pbar.close()

    # 🧠 Save owner location cache
    save_json(owner_cache, cache_file)
    print(f"🧠 Cached {len(owner_cache)} owner locations")
    print(f"🎯 Final collected {len(localized_repos)} repositories (across {page-1} pages)\n")

    if not localized_repos:
        print("❌ No repositories found for this location.")
        return

    # 🧮 Calculate influence scores
    max_stars = max((r["stargazers_count"] for r in localized_repos), default=1)
    max_forks = max((r["forks_count"] for r in localized_repos), default=1)
    max_watchers = max((r["watchers_count"] for r in localized_repos), default=1)

    results = []
    for repo in localized_repos:
        name = repo["full_name"]
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        watchers = repo.get("watchers_count", 0)
        issues = repo.get("open_issues_count", 0)
        created = repo.get("created_at", "2020-01-01T00:00:00Z")
        language = repo.get("language") or "Unknown"

        S = normalize(stars, max_stars)
        F = normalize(forks, max_forks)
        W = normalize(watchers, max_watchers)
        T = age_weight(created)
        H = health_score(issues)
        score = 0.4 * S + 0.25 * F + 0.15 * W + 0.10 * T + 0.10 * H

        results.append({
            "name": name,
            "owner": repo["owner"]["login"],
            "stars": stars,
            "forks": forks,
            "watchers": watchers,
            "issues": issues,
            "created_at": created,
            "language": language,
            "score": round(score, 4),
            "html_url": repo.get("html_url")
        })

    # 🏆 Group by language
    language_groups = {"Python": [], "C++": [], "Other": []}
    for r in results:
        lang = r["language"]
        if lang == "Python":
            language_groups["Python"].append(r)
        elif lang == "C++":
            language_groups["C++"].append(r)
        else:
            language_groups["Other"].append(r)
    
    # 📦 Fetch PyPI data for Python projects if requested
    if args.fetch_pypi and PYPI_AVAILABLE and len(language_groups["Python"]) > 0:
        print(f"\n📦 Fetching PyPI download statistics for {len(language_groups['Python'])} Python projects...")
        pypi_client = PyPIClient()
        
        for repo in tqdm(language_groups["Python"], desc="PyPI lookup", ncols=80):
            pypi_info = pypi_client.get_package_info(repo["name"])
            repo["pypi_package"] = pypi_info["package_name"]
            repo["pypi_exists"] = pypi_info["exists"]
            repo["pypi_downloads_month"] = pypi_info["downloads_month"]
        
        print(f"✅ PyPI data fetched for {sum(1 for r in language_groups['Python'] if r.get('pypi_exists', False))} packages")
    
    # 🔢 Recalculate scores with PyPI/Release data if available
    if args.fetch_pypi:
        # Get max values for normalization
        max_downloads = max((r.get("pypi_downloads_month", 0) for r in language_groups["Python"]), default=1)
        
        print(f"\n🔢 Recalculating scores with integrated data...")
        print(f"   Max PyPI downloads/month: {max_downloads:,}")
        
        # Recalculate Python scores with PyPI data
        for repo in language_groups["Python"]:
            downloads = repo.get("pypi_downloads_month", 0)
            if downloads > 0:
                # 40% GitHub + 60% PyPI
                import math
                pypi_score = math.log10(downloads + 1) / math.log10(max_downloads + 1)
                repo["pypi_score"] = round(pypi_score, 4)
                repo["final_score"] = round(0.4 * repo["score"] + 0.6 * pypi_score, 4)
                repo["score_type"] = "github+pypi"
            else:
                repo["final_score"] = repo["score"]
                repo["score_type"] = "github_only"
        
        # Sort by final_score
        language_groups["Python"] = sorted(language_groups["Python"], key=lambda x: x.get("final_score", x["score"]), reverse=True)
    
    # Sort other language groups by score
    for lang in ["C++", "Other"]:
        language_groups[lang] = sorted(language_groups[lang], key=lambda x: x["score"], reverse=True)
        # Add final_score for consistency
        for repo in language_groups[lang]:
            if "final_score" not in repo:
                repo["final_score"] = repo["score"]
                repo["score_type"] = "github_only"
    
    # Create output structure
    output_data = {
        "Python": language_groups["Python"][:args.topk],
        "C++": language_groups["C++"][:args.topk],
        "Other": language_groups["Other"][:args.topk],
        "metadata": {
            "total_repos": len(results),
            "by_language": {
                "Python": len(language_groups["Python"]),
                "C++": len(language_groups["C++"]),
                "Other": len(language_groups["Other"])
            },
            "location": args.location,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    }

    # Print summary
    print("\n🏆 Top repositories by Seattle-based developers (by language):")
    print("=" * 80)
    for lang in ["Python", "C++", "Other"]:
        count = output_data["metadata"]["by_language"][lang]
        print(f"\n📊 {lang} ({count} projects)")
        print("-" * 80)
        
        # Adjust header based on whether PyPI data is included
        if lang == "Python" and args.fetch_pypi:
            print(f"{'Repo':30s} {'Stars':>6s} {'Downloads':>12s} {'Final':>8s} {'Type':>12s}")
        else:
            print(f"{'Repo':38s} {'Stars':>6s} {'Forks':>6s} {'Score':>8s}")
        print("-" * 80)
        
        for r in output_data[lang][:10]:  # Show top 10 per language
            if lang == "Python" and args.fetch_pypi and r.get("pypi_downloads_month", 0) > 0:
                downloads_str = f"{r['pypi_downloads_month']:,}"[:10]
                score_display = r.get("final_score", r["score"])
                score_type = r.get("score_type", "github")[:10]
                print(f"{r['name'][:28]:30s} {r['stars']:6d} {downloads_str:>12s} {score_display:8.3f} {score_type:>12s}")
            else:
                score_display = r.get("final_score", r["score"])
                print(f"{r['name'][:36]:38s} {r['stars']:6d} {r['forks']:6d} {score_display:8.3f}")
    print("=" * 80)

    save_json(output_data, f"data/ranked_by_language_{args.location.lower()}.json")
    
    # Also save legacy format for backward compatibility
    all_ranked = sorted(results, key=lambda x: x["score"], reverse=True)[:args.topk]
    save_json(all_ranked, f"data/ranked_project_local_{args.location.lower()}.json")
    
    print("🏁 Done! Language-based ranking complete.")

if __name__ == "__main__":
    main()
