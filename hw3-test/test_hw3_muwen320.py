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
    Holding all other fields constant, a project with extremely many open issues
    should not receive a *higher* GitHub score than the same project with very few issues.
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

    project_few_issues = {**base, "open_issues": 1}
    project_many_issues = {**base, "open_issues": 5000}

    score_few = calculate_github_score(project_few_issues, 10_000, 5_000, 2_000)
    score_many = calculate_github_score(project_many_issues, 10_000, 5_000, 2_000)

    assert score_many <= score_few, (
        f"Expected score with many issues <= score with few issues, "
        f"got many={score_many}, few={score_few}"
    )


def test_age_factor_pattern_time_ordering():
    """
    author: Muwen320
    reviewer: Chase-Zou
    category: pattern test

    Pattern test:
    Check the monotonic ordering of `age_factor()`:
    older projects should produce age factor values that are
    not smaller than those of newer projects.
    """
    now = datetime.now(timezone.utc)

    created_new = (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    created_mid = (now - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    created_old = (now - timedelta(days=5 * 365)).strftime("%Y-%m-%dT%H:%M:%SZ")

    new_score = age_factor(created_new)
    mid_score = age_factor(created_mid)
    old_score = age_factor(created_old)

    for s in (new_score, mid_score, old_score):
        assert 0.0 <= s <= 1.0

    assert new_score <= mid_score <= old_score, (
        f"Expected new <= mid <= old, got "
        f"new={new_score}, mid={mid_score}, old={old_score}"
    )