import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.classify_languages import classify_by_name

def test_smoke_basic_repo_name():
    """
    author: Muwen320
    reviewer: Wenshu0206
    category: smoke test
    """
    name = "my-django-app"
    result = classify_by_name(name)
    assert isinstance(result, str)
    assert result != ""


def test_one_shot_known_language_mapping():
    """
    author: Muwen320
    reviewer: Wenshu0206
    category: one-shot test
    """
    name = "system-design-primer"
    result = classify_by_name(name)
    assert result == "Python"


def test_edge_numeric_and_very_long():
    """
    author: Muwen320
    reviewer: Chase-Zou
    category: edge test
    """
    name = "1234567890-" + "x" * 200
    result = classify_by_name(name)
    allowed = {"Python", "C++", "Other", "TypeScript", "JavaScript", "C#"}
    assert result in allowed


def test_pattern_many_python_repos():
    """
    author: Muwen320
    reviewer: Chase-Zou
    category: pattern test
    """
    python_like = [
        "django-rest-framework",
        "flask-example",
        "pytorch-tutorial",
    ]
    for name in python_like:
        result = classify_by_name(name)
        assert result == "Python"