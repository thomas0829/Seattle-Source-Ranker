"""
Scoring algorithms for Seattle Source Ranker.

This module provides the SSR (Seattle Source Ranker) scoring algorithm
and related utility functions for project ranking.
"""

import math
from datetime import datetime, timezone

# PyPI scoring configuration
PYPI_TIER1_MULTIPLIER = 1.05  # Any PyPI package
PYPI_TIER2_MULTIPLIER = 1.10  # Top 15k PyPI package


def normalize(value, max_value):
    """Normalize value to 0-1 range"""
    return value / max_value if max_value > 0 else 0


def log_normalize(value, base=10):
    """Logarithmic normalization for better score distribution"""
    return math.log10(value + 1) / math.log10(base)


def age_factor(created_at):
    """
    Calculate age factor (0-1 range)
    Mature projects (2-8 years) get higher scores
    """
    try:
        created_time = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        years = (datetime.now(timezone.utc) - created_time).days / 365.25

        # Peak score at 3-5 years, decrease for too old/new
        if years < 0.5:
            return 0.3  # Too new
        if years < 2:
            return 0.6 + (years - 0.5) * 0.2  # Growing: 0.6-0.9
        if years < 5:
            return 0.9 + (years - 2) * 0.033  # Peak: 0.9-1.0
        if years < 8:
            return 1.0 - (years - 5) * 0.05  # Mature: 1.0-0.85
        return 0.7 - min((years - 8) * 0.03, 0.4)  # Declining: 0.7-0.3
    except (ValueError, TypeError):
        return 0.5


def activity_factor(pushed_at, created_at):
    """
    Calculate recent activity factor (0-1 range)
    Recent updates indicate active maintenance
    """
    try:
        pushed_time = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        created_time = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

        days_since_push = (datetime.now(timezone.utc) - pushed_time).days
        project_age_days = (datetime.now(timezone.utc) - created_time).days

        # Avoid division by zero
        if project_age_days < 1:
            return 1.0

        # Recent activity is good
        if days_since_push < 30:
            return 1.0
        if days_since_push < 90:
            return 0.9
        if days_since_push < 180:
            return 0.8
        if days_since_push < 365:
            return 0.6
        if days_since_push < 730:
            return 0.4
        return 0.2
    except (ValueError, TypeError):
        return 0.5


def health_factor(open_issues, stars):
    """
    Calculate project health (0-1 range)
    Issues relative to popularity
    """
    if stars < 10:
        return 1.0 if open_issues < 5 else 0.8

    # Issue ratio relative to stars
    issue_ratio = open_issues / (stars + 1)

    if issue_ratio < 0.01:
        return 1.0
    if issue_ratio < 0.05:
        return 0.9
    if issue_ratio < 0.1:
        return 0.8
    if issue_ratio < 0.2:
        return 0.6
    return 0.4


def calculate_github_score(project, _max_stars=None, _max_forks=None, _max_watchers=None, 
                          on_pypi=False, on_top_pypi=False):
    """
    Calculate SSR score for a GitHub project
    
    Args:
        project (dict): Project data with metrics
        _max_stars: (deprecated) Kept for backward compatibility
        _max_forks: (deprecated) Kept for backward compatibility
        _max_watchers: (deprecated) Kept for backward compatibility
        on_pypi (bool): Whether the project is on PyPI
        on_top_pypi (bool): Whether the project is in top 15k PyPI packages
        
    Returns:
        float: SSR score (0-1,000,000 range)
    """
    # Extract metrics with defaults
    stars = project.get('stars', 0)
    forks = project.get('forks', 0)
    watchers = project.get('watchers', 0)
    open_issues = project.get('open_issues', 0)
    created_at = project.get('created_at', '')
    pushed_at = project.get('pushed_at', '')
    
    # Base popularity metrics (70%)
    star_score = log_normalize(stars, 100000) * 0.40
    fork_score = log_normalize(forks, 10000) * 0.20
    watcher_score = log_normalize(watchers, 10000) * 0.10
    
    # Quality factors (30%)
    age_score = age_factor(created_at) * 0.10
    activity_score = activity_factor(pushed_at, created_at) * 0.10
    health_score = health_factor(open_issues, stars) * 0.10
    
    # Calculate base score
    total_score = (
        star_score +
        fork_score +
        watcher_score +
        age_score +
        activity_score +
        health_score
    )
    
    # Scale to 0-1,000,000
    base_score = total_score * 1000000
    
    # Apply tiered PyPI multipliers
    final_score = base_score
    if on_pypi:
        final_score *= PYPI_TIER1_MULTIPLIER
    if on_top_pypi:
        final_score *= PYPI_TIER2_MULTIPLIER
    
    return round(final_score)


__all__ = [
    "normalize",
    "log_normalize",
    "age_factor",
    "activity_factor",
    "health_factor",
    "calculate_github_score",
]
