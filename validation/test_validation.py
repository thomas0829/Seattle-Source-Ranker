import os
import pandas as pd


# ============================================================
#   Functions
# ============================================================

def chase_smoke_test_json_to_csv_output():
    import importlib
    import json_to_csv

    importlib.reload(json_to_csv)
    out_path = json_to_csv.OUTPUT_PATH

    if not os.path.exists(out_path):
        return False

    df = pd.read_csv(out_path)
    expected = {"name_with_owner", "stars", "forks", "watchers"}
    return len(df) > 0 and expected.issubset(df.columns)


def chase_one_shot_test_metric_quality_single_repo():
    from validate_repo_metrics import compute_metric_quality

    df = pd.DataFrame([{
        "stars": 10,
        "forks": 3,
        "watchers": 10,
        "open_issues": 0,
    }])

    metrics = compute_metric_quality(df, ["stars", "forks", "watchers", "open_issues"])

    return (
        metrics["stars"]["total"] == 1
        and metrics["stars"]["missing"] == 0
        and metrics["stars"]["negatives"] == 0
        and metrics["forks"]["total"] == 1
        and metrics["forks"]["missing"] == 0
        and metrics["forks"]["negatives"] == 0
    )


def chase_edge_test_metric_quality_negative_and_missing():
    from validate_repo_metrics import compute_metric_quality, check_consistency_rules

    df = pd.DataFrame([{
        "stars": None,
        "forks": -5,
        "watchers": None,
        "open_issues": -1,
        "description": "",
    }])

    metrics = compute_metric_quality(df, ["forks", "open_issues"])
    consistency = check_consistency_rules(df)

    return (
        metrics["forks"]["negatives"] >= 1
        and metrics["open_issues"]["negatives"] >= 1
        and consistency["open_issues_non_negative"]["negative_count"] >= 1
    )


def chase_pattern_test_outlier_detection_pattern():
    from validate_repo_metrics import detect_outlier_repos

    df = pd.DataFrame([
        {
            "name_with_owner": "test/high-star-empty-desc",
            "description": "",
            "stars": 1000,
            "forks": 10,
            "open_issues": 0,
        },
        {
            "name_with_owner": "normal/repo",
            "description": "normal project",
            "stars": 5,
            "forks": 1,
            "open_issues": 0,
        },
    ])

    outliers = detect_outlier_repos(df, top_n=10)
    names = set(outliers.get("name_with_owner", []))

    return (
        "test/high-star-empty-desc" in names
        and "normal/repo" not in names
    )


# ============================================================
#   pytest 
# ============================================================

def test_smoke():
    assert chase_smoke_test_json_to_csv_output()


def test_single_repo_quality():
    assert chase_one_shot_test_metric_quality_single_repo()


def test_negative_and_missing():
    assert chase_edge_test_metric_quality_negative_and_missing()


def test_outlier_pattern():
    assert chase_pattern_test_outlier_detection_pattern()
