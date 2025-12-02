#!/usr/bin/env python3
"""
Homework 3 - Testing Assignment
Author: thomas0829
Tests for Seattle Source Ranker project
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.token_manager import TokenManager
from scripts.generate_frontend_data import (
    normalize,
    age_factor,
    calculate_github_score
)


def test_token_manager_basic_smoke():
    """
    author: thomas0829
    reviewer: Wenshu0206
    category: smoke test
    
    Basic smoke test to ensure TokenManager initializes without crashing
    """
    tokens = ['ghp_test_token_1', 'ghp_test_token_2']
    tm = TokenManager(tokens)
    assert tm is not None
    assert tm.get_token_count() == 2


def test_normalize_specific_value():
    """
    author: thomas0829
    reviewer: Chase-Zou
    category: one-shot test
    
    Test normalization with specific known input/output pair
    """
    # Testing that 75 normalized by max 150 equals exactly 0.5
    result = normalize(75, 150)
    assert result == 0.5, f"Expected 0.5 but got {result}"


def test_age_factor_edge_case_zero():
    """
    author: thomas0829
    reviewer: Chase-Zou
    category: edge test
    
    Test edge case: project created at the exact current moment
    """
    # Create a timestamp for right now
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Age factor for brand new project should be very low
    score = age_factor(now)
    
    # Brand new projects (0 days old) should score very low
    assert 0 <= score <= 0.3, f"Brand new project should score <= 0.3, got {score}"


def test_github_score_pattern_increases_with_stars():
    """
    author: thomas0829
    reviewer: Wenshu0206
    category: pattern test
    
    Test pattern: as stars increase, score should generally increase
    (holding other factors constant)
    """
    # Base project template
    base_project = {
        'forks': 100,
        'watchers': 50,
        'created_at': (datetime.now(timezone.utc) - timedelta(days=3*365)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        'pushed_at': (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        'open_issues': 10
    }
    
    # Test with increasing star counts
    scores = []
    star_counts = [100, 500, 1000, 5000, 10000]
    
    for stars in star_counts:
        project = base_project.copy()
        project['stars'] = stars
        score = calculate_github_score(project, 20000, 5000, 1000)
        scores.append(score)
    
    # Verify pattern: scores should be non-decreasing
    for i in range(len(scores) - 1):
        assert scores[i] <= scores[i + 1], \
            f"Score should increase with stars: {scores[i]} (stars={star_counts[i]}) > {scores[i + 1]} (stars={star_counts[i + 1]})"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
