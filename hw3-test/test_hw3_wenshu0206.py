#!/usr/bin/env python3
"""
Homework 3 - Testing Assignment (Enhanced Version)
Author: Wenshu0206
Tests for classify_language()
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_frontend_data import classify_language


def test_classify_smoke_multiple_inputs():
    """
    author: Wenshu0206
    reviewer: thomas0829
    category: smoke test

    Smoke test: ensure function runs on different language inputs without crashing,
    and returns valid tuple outputs with correct structure.
    """
    languages = ["Python", "JavaScript", "Java", "Go"]
    results = [classify_language(lang) for lang in languages]

    assert all(isinstance(r, tuple) and len(r) == 3 for r in results)
    assert len(results) == 4


def test_one_shot_python_top10():
    """
    author: Wenshu0206
    reviewer: Muwen320
    category: one-shot test

    One-shot: Python is a top 10 language and should be classified correctly.
    """
    category, original, is_true_other = classify_language("Python")

    assert category == "Python"
    assert original == "Python"
    assert is_true_other == False


def test_one_shot_known_language_mapping():
    """
    author: Wenshu0206
    reviewer: thomas0829
    category: one-shot test

    One-shot: JavaScript should map to top 10 category.
    """
    category, original, is_true_other = classify_language("JavaScript")
    assert category == "JavaScript"
    assert is_true_other == False


def test_edge_null_and_empty():
    """
    author: Wenshu0206
    reviewer: Muwen320
    category: edge test

    Edge: null/None and empty string should return 'Other' with is_true_other=True.
    """
    result_none = classify_language(None)
    result_empty = classify_language("")

    assert result_none == ('Other', 'Other', True)
    assert result_empty == ('Other', 'Other', True)


def test_pattern_case_insensitive():
    """
    author: Wenshu0206
    reviewer: thomas0829
    category: pattern test

    Pattern: language classification should be case-insensitive for top 10 languages.
    """
    test_cases = [
        "python",
        "PYTHON",
        "Python",
        "PyThOn"
    ]

    results = [classify_language(lang) for lang in test_cases]

    # All should map to Python category
    assert all(r[0] == "Python" for r in results)
    # All should preserve original input
    assert [r[1] for r in results] == test_cases
    # None should be marked as true other
    assert all(r[2] == False for r in results)
