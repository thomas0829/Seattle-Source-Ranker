#!/usr/bin/env python3
"""
Homework 3 - Testing Assignment
Author: Muwen320

Tests for Seattle Source Ranker project modules:
- calculate_github_score
- normalize
- age_factor
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure project root is in Python path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.token_manager import TokenManager
from scripts.generate_frontend_data import (
    normalize,
    age_factor,
    calculate_github_score,
)


def test_github_score_smoke_basic():
    """
    author: Muwen320
    reviewer: Wenshu0206
    category: smoke test

    Smoke test:
    Verify that `calculate_github_score()` can run on a valid project dictionary
    without raising errors, and returns a non-negative numeric value.
    """
    now = datetime.now(timezone.utc)
    created = (now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pushed = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    project = {
        "stars": 50,
        "forks": 20,
        "watchers": 10,
        "open_issues": 5,
        "created_at": created,
        "pushed_at": pushed,
    }

    score = calculate_github_score(project, max_stars=1000, max_forks=500, max_watchers=200)

    assert isinstance(score, (int, float))
    assert score >= 0


def test_normalize_one_shot_full_value():
    """
    author: Muwen320
    reviewer: Wenshu0206
    category: one-shot test

    One-shot test:
    Fixed input–output pair. When value == max_value, normalization
    should return exactly 1.0.
    """
    result = normalize(100, 100)
    assert result == 1.0, f"Expected 1.0 but got {result}"


def test_github_score_edge_many_issues():
    """
    author: Muwen320
    reviewer: Chase-Zou
    category: edge test

    Edge test:
    Projects with extremely many issues should not receive a higher score,
    and ideally the score should decrease when issue count becomes very large.
    """
    now = datetime.now(timezone.utc)
    created = (now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pushed = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    base = {
        "stars": 500,
        "forks": 100,
        "watchers": 80,
        "created_at": created,
        "pushed_at": pushed,
    }

    project_few = {**base, "open_issues": 1}
    project_many = {**base, "open_issues": 5000}

    score_few = calculate_github_score(project_few, 10_000, 5_000, 2_000)
    score_many = calculate_github_score(project_many, 10_000, 5_000, 2_000)

    # Must not increase
    assert score_many <= score_few

    # And in realistic scoring, many issues should reduce score
    assert score_many < score_few or abs(score_many - score_few) < 1e-6


def test_age_factor_pattern_time_ordering():
    """
    author: Muwen320
    reviewer: Chase-Zou
    category: pattern test

    Pattern test:
    Older projects should not receive a smaller age factor.
    Uses multiple timestamps to better verify monotonic behavior.
    """
    now = datetime.now(timezone.utc)

    timestamps = [
        (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        (now - timedelta(days=100)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        (now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        (now - timedelta(days=1000)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        (now - timedelta(days=2000)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    ]

    scores = [age_factor(ts) for ts in timestamps]

    # All scores must be valid and between 0 and 1
    for s in scores:
        assert 0.0 <= s <= 1.0

    # Check non-decreasing order
    for i in range(len(scores) - 1):
        assert scores[i] <= scores[i + 1], \
            f"Expected monotonic increase: {scores}"