#!/usr/bin/env python3
"""
Homework 3 - Testing Assignment (Enhanced Version)
Author: Wenshu0206
Tests for classify_by_name()
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.classify_languages import classify_by_name


def test_classify_smoke_multiple_inputs():
    """
    author: Wenshu0206
    reviewer: thomas0829
    category: smoke test

    Smoke test: ensure function runs on simple names without crashing,
    and returns valid string outputs.
    """
    names = ["repo", "python-utils", "opencv-lib", "vscode"]
    results = [classify_by_name(n) for n in names]

    assert all(isinstance(r, str) for r in results)
    assert len(results) == 4


def test_one_shot_python_keyword():
    """
    author: Wenshu0206
    reviewer: Muwen320
    category: one-shot test

    One-shot: a single known Python keyword should map to Python.
    """
    name = "my-django-app"
    result = classify_by_name(name)

    assert result == "Python"
    assert isinstance(result, str)


def test_one_shot_known_language_mapping():
    """
    author: Wenshu0206
    reviewer: thomas0829
    category: one-shot test

    One-shot: known mapping from project name dictionary.
    """
    result = classify_by_name("system-design-primer")
    assert result == "Python"


def test_edge_numeric_and_very_long():
    """
    author: Wenshu0206
    reviewer: Muwen320
    category: edge test

    Edge: non-alphabetic name and extremely long name.
    """
    numeric = classify_by_name("123456789")
    long_name = "python" + ("x" * 2000)
    long_result = classify_by_name(long_name)

    assert numeric == "Other"

    assert long_result == "Python"
    assert len(long_name) > 2000


def test_pattern_tensorflow_priority():
    """
    author: Wenshu0206
    reviewer: thomas0829
    category: pattern test

    Pattern: all names containing 'tensorflow' should map to Python
    even if they also contain other language keywords.
    """
    tensorflow_names = [
        "tensorflow-utils",
        "tensorflow-models",
        "my-tensorflow-project",
        "tensorflow-cpp",
        "tensorflow"
    ]

    results = [classify_by_name(n) for n in tensorflow_names]

    assert all(r == "Python" for r in results)
