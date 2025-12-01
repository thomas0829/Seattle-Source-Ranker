#!/usr/bin/env python3
"""
Homework 3 - Testing Assignment
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

    Smoke test: ensure function runs on multiple simple names.
    """
    names = ["repo", "python-utils", "opencv-lib", "vscode"]
    results = [classify_by_name(n) for n in names]

    assert all(isinstance(r, str) for r in results)
    assert len(results) == 4
    assert results[0] == "Other"
    assert results[3] == "TypeScript"

def test_one_shot_python_keyword():
    """
    author: Wenshu0206
    reviewer: Chase-Zou
    category: one-shot test
    """
    name = "my-django-app"
    result = classify_by_name(name)

    assert result == "Python"
    assert result != "C++"
    assert isinstance(result, str)

def test_one_shot_known_language_mapping():
    """
    author: Wenshu0206
    reviewer: Muwen320
    category: one-shot test

    Known language mapping: system-design-primer → Python.
    """
    result = classify_by_name("system-design-primer")

    assert result == "Python"
    assert result in ["Python", "C++", "Other", "TypeScript", "JavaScript", "C#"]

def test_edge_numeric_and_very_long():
    """
    author: Wenshu0206
    reviewer: Chase-Zou
    category: edge test
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
    reviewer: Muwen320
    category: pattern test

    tensorflow appears in BOTH Python and C++ keywords.
    Python should win due to ordering.
    """
    name = "tensorflow-utils"
    result = classify_by_name(name)

    assert result == "Python"
    assert result != "C++"
    assert isinstance(result, str)

