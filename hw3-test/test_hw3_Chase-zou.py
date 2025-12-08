import os
import pandas as pd


# ============================================================
#   Chase Zou - HW3 validation tests
#   Each test uses pytest-style asserts + required docstrings
# ============================================================


def test_chase_smoke_json_to_csv_module():
    """
    author: Chase-Zou
    reviewer: thomas0829
    category: smoke test

    Smoke test: verify json_to_csv module can be imported without
    crashing and exposes a string OUTPUT_PATH attribute. This is a
    minimal "can it run?" check and does NOT inspect file contents.
    """
    import importlib
    import json_to_csv

    # Reload to avoid stale state during repeated pytest runs
    importlib.reload(json_to_csv)

    # Basic API surface check
    assert hasattr(json_to_csv, "OUTPUT_PATH")
    assert isinstance(json_to_csv.OUTPUT_PATH, str)


def test_chase_one_shot_metric_quality_single_repo():
    """
    author: Chase-Zou
    reviewer: thomas0829
    category: one-shot test

    One-shot test: given a single, clean repository row with valid
    non-negative metrics, compute_metric_quality should:
      - count exactly one record for each metric column
      - report zero missing values
      - report zero negative values
    """
    from validate_repo_metrics import compute_metric_quality

    # Single, clean repository
    df = pd.DataFrame(
        [
            {
                "stars": 10,
                "forks": 3,
                "watchers": 10,
                "open_issues": 0,
            }
        ]
    )

    metric_cols = ["stars", "forks", "watchers", "open_issues"]
    metrics = compute_metric_quality(df, metric_cols)

    # For every metric column we expect:
    # - total == 1
    # - missing == 0
    # - negatives == 0
    for col in metric_cols:
        assert col in metrics
        assert metrics[col]["total"] == 1
        assert metrics[col]["missing"] == 0
        assert metrics[col]["negatives"] == 0


def test_chase_edge_metric_quality_negative_and_missing():
    """
    author: Chase-Zou
    reviewer: thomas0829
    category: edge test

    Edge test: construct a row with missing values (None) and
    negative values to ensure:
      - compute_metric_quality counts negatives correctly
      - check_consistency_rules flags open_issues < 0 via
        an 'open_issues_non_negative' rule (or similar).
    """
    from validate_repo_metrics import compute_metric_quality, check_consistency_rules

    df = pd.DataFrame(
        [
            {
                "stars": None,       # missing
                "forks": -5,         # negative
                "watchers": None,    # missing
                "open_issues": -1,   # negative
                "description": "",
            }
        ]
    )

    # We only need to check forks and open_issues here, which are negative.
    metric_cols = ["forks", "open_issues"]
    metrics = compute_metric_quality(df, metric_cols)

    # Negatives should be counted for forks and open_issues
    assert metrics["forks"]["negatives"] >= 1
    assert metrics["open_issues"]["negatives"] >= 1

    # Consistency rules should flag negative open_issues
    consistency = check_consistency_rules(df)
    assert "open_issues_non_negative" in consistency
    assert consistency["open_issues_non_negative"]["negative_count"] >= 1


def test_chase_pattern_outlier_detection_pattern():
    """
    author: Chase-Zou
    reviewer: thomas0829
    category: pattern test

    Pattern test: consistent rule = repos with very high stars AND
    empty description should always be outliers.
    Repos with non-empty descriptions and moderate stars should
    not be flagged as outliers.
    """
    from validate_repo_metrics import detect_outlier_repos

    df = pd.DataFrame(
        [
            # Outliers (high stars + empty description)
            {
                "name_with_owner": "test/high-star-empty-desc-1",
                "description": "",
                "stars": 2000,
                "forks": 20,
                "open_issues": 0,
            },
            {
                "name_with_owner": "test/high-star-empty-desc-2",
                "description": "",
                "stars": 1500,
                "forks": 15,
                "open_issues": 1,
            },
            # Normal repos
            {
                "name_with_owner": "normal/repo-1",
                "description": "normal project 1",
                "stars": 10,
                "forks": 3,
                "open_issues": 0,
            },
            {
                "name_with_owner": "normal/repo-2",
                "description": "normal project 2",
                "stars": 25,
                "forks": 5,
                "open_issues": 2,
            },
            {
                "name_with_owner": "normal/repo-3",
                "description": "normal project 3",
                "stars": 40,
                "forks": 8,
                "open_issues": 0,
            },
        ]
    )

    outliers = detect_outlier_repos(df, top_n=10)

    if isinstance(outliers, pd.DataFrame):
        names = set(outliers["name_with_owner"].tolist())
    else:
        names = set(outliers.get("name_with_owner", []))

    # Expectations:
    assert "test/high-star-empty-desc-1" in names
    assert "test/high-star-empty-desc-2" in names

    # Normal repos must NOT be outliers
    assert "normal/repo-1" not in names
    assert "normal/repo-2" not in names
    assert "normal/repo-3" not in names

