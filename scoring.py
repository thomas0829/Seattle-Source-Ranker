"""
Enhanced scoring system with PyPI and GitHub Release download integration
"""
from typing import Dict, List
import math

def normalize(value: float, max_value: float) -> float:
    """Normalize value to 0-1 range"""
    return value / max_value if max_value > 0 else 0

def log_normalize(value: float, max_value: float) -> float:
    """
    Logarithmic normalization for values with huge ranges (like downloads)
    """
    if value <= 0 or max_value <= 0:
        return 0
    return math.log10(value + 1) / math.log10(max_value + 1)

def calculate_github_score(repo: Dict, max_stars: int, max_forks: int, max_watchers: int) -> float:
    """
    Calculate base GitHub score (stars, forks, watchers, age, health)
    Returns score in 0-1 range
    """
    from main import normalize, age_weight, health_score
    
    stars = repo.get("stars", 0)
    forks = repo.get("forks", 0)
    watchers = repo.get("watchers", 0)
    issues = repo.get("issues", 0)
    created = repo.get("created_at", "2020-01-01T00:00:00Z")
    
    S = normalize(stars, max_stars)
    F = normalize(forks, max_forks)
    W = normalize(watchers, max_watchers)
    T = age_weight(created)
    H = health_score(issues)
    
    # Original GitHub-only score
    github_score = 0.4 * S + 0.25 * F + 0.15 * W + 0.10 * T + 0.10 * H
    return github_score

def calculate_pypi_score(downloads_month: int, max_downloads: int) -> float:
    """
    Calculate PyPI download score
    Uses log normalization due to huge range in download numbers
    """
    if downloads_month <= 0:
        return 0
    return log_normalize(downloads_month, max_downloads)

def calculate_release_score(release_downloads: int, max_release_downloads: int) -> float:
    """
    Calculate GitHub Release download score for C++ projects
    """
    if release_downloads <= 0:
        return 0
    return log_normalize(release_downloads, max_release_downloads)

def calculate_final_score(repo: Dict, language: str, 
                         max_stars: int, max_forks: int, max_watchers: int,
                         max_downloads: int = 1, max_release_downloads: int = 1) -> Dict:
    """
    Calculate final weighted score based on language
    
    Python: 40% GitHub + 60% PyPI downloads
    C++: 70% GitHub + 30% Release downloads
    Other: 100% GitHub
    """
    github_score = calculate_github_score(repo, max_stars, max_forks, max_watchers)
    
    if language == "Python":
        downloads = repo.get("pypi_downloads_month", 0)
        if downloads > 0:
            pypi_score = calculate_pypi_score(downloads, max_downloads)
            final_score = 0.4 * github_score + 0.6 * pypi_score
            score_type = "github+pypi"
        else:
            final_score = github_score
            score_type = "github_only"
    
    elif language == "C++":
        release_downloads = repo.get("release_downloads", 0)
        if release_downloads > 0:
            release_score = calculate_release_score(release_downloads, max_release_downloads)
            final_score = 0.7 * github_score + 0.3 * release_score
            score_type = "github+releases"
        else:
            final_score = github_score
            score_type = "github_only"
    
    else:
        final_score = github_score
        score_type = "github_only"
    
    return {
        "final_score": round(final_score, 4),
        "github_score": round(github_score, 4),
        "score_type": score_type
    }

def enhance_repos_with_scores(repos: List[Dict], language: str,
                              max_stats: Dict) -> List[Dict]:
    """
    Add enhanced scores to all repos for a given language
    """
    for repo in repos:
        scores = calculate_final_score(
            repo, language,
            max_stats["max_stars"],
            max_stats["max_forks"],
            max_stats["max_watchers"],
            max_stats.get("max_downloads", 1),
            max_stats.get("max_release_downloads", 1)
        )
        repo.update(scores)
    
    return repos
