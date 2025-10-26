import argparse
import os
import json
import requests
from datetime import datetime, timezone
from tqdm import tqdm  # Progress bar for better UX
from github_client import GitHubClient

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
    parser = argparse.ArgumentParser(description="Seattle-Source-Ranker (cached with progress bar)")
    parser.add_argument("--location", type=str, default="Seattle", help="Developer location keyword (e.g. Seattle)")
    parser.add_argument("--topk", type=int, default=50, help="Number of Seattle-based repos to collect")
    parser.add_argument("--max-pages", type=int, default=20, help="Max number of pages to fetch (safety cap)")
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
            "score": round(score, 4),
            "html_url": repo.get("html_url")
        })

    # 🏆 Sort & Output
    ranked = sorted(results, key=lambda x: x["score"], reverse=True)
    top_repos = ranked[:args.topk]

    print("🏆 Top repositories by Seattle-based developers:")
    print("--------------------------------------------")
    print(f"{'Repo':38s} {'Stars':>6s} {'Forks':>6s} {'Score':>8s}")
    print("--------------------------------------------")
    for r in top_repos:
        print(f"{r['name'][:36]:38s} {r['stars']:6d} {r['forks']:6d} {r['score']:8.3f}")
    print("--------------------------------------------")

    save_json(top_repos, f"data/ranked_project_local_{args.location.lower()}.json")
    print("🏁 Done! Project-based localization ranking complete.")

if __name__ == "__main__":
    main()
