import os
import json
import pandas as pd


def chase_smoke_test_json_to_csv_output():
    """
    author: chase
    reviewer:
    category: smoke test

    description:
        Smoke test for the JSON -> CSV conversion pipeline.

        This test checks that the json_to_csv module can be imported and that
        its OUTPUT_PATH CSV file exists and contains some basic expected
        columns. The goal is to verify that the conversion script runs
        end-to-end without crashing and produces a non-empty CSV.
    """
    try:
        import importlib
        import json_to_csv  # uses INPUT_PATH and OUTPUT_PATH from the script

        # Reload to ensure that the top-level conversion code has been executed.
        importlib.reload(json_to_csv)

        out_path = json_to_csv.OUTPUT_PATH

        if not os.path.exists(out_path):
            return False

        df = pd.read_csv(out_path)

        # Basic non-trivial check:
        # - file is not empty
        # - has some core repo columns
        expected_cols = {"name_with_owner", "stars", "forks", "watchers"}
        return (len(df) > 0) and expected_cols.issubset(set(df.columns))
    except Exception:
        # If anything goes wrong in the pipeline, the smoke test fails.
        return False



def chase_one_shot_test_metric_quality_single_repo():
    """
    author: chase
    reviewer:
    category: one-shot test

    description:
        One-shot test for compute_metric_quality using a single, fully valid
        synthetic repo record. The expected behavior is:
        - total count = 1
        - no missing values
        - no negative values
        for the selected metric columns.
    """
    from validate_repo_metrics import compute_metric_quality

    # Single "normal" repo entry with consistent metrics
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

    metrics = compute_metric_quality(df, ["stars", "forks", "watchers", "open_issues"])

    stars_info = metrics["stars"]
    forks_info = metrics["forks"]

    # Non-trivial: we check multiple fields of the summary
    return (
        stars_info["total"] == 1
        and stars_info["missing"] == 0
        and stars_info["negatives"] == 0
        and forks_info["total"] == 1
        and forks_info["missing"] == 0
        and forks_info["negatives"] == 0
    )



def chase_edge_test_metric_quality_negative_and_missing():
    """
    author: chase
    reviewer:
    category: edge test

    description:
        Edge-case test for metric quality and consistency rules.

        This test constructs a repo row with:
        - missing stars
        - negative forks
        - negative open_issues

        It then verifies that:
        - compute_metric_quality reports at least one negative value
          for forks and open_issues
        - check_consistency_rules flags negative open_issues in its
          open_issues_non_negative rule.
    """
    from validate_repo_metrics import compute_metric_quality, check_consistency_rules

    df = pd.DataFrame(
        [
            {
                "stars": None,
                "forks": -5,
                "watchers": None,
                "open_issues": -1,
                "description": "",
            }
        ]
    )

    metrics = compute_metric_quality(df, ["forks", "open_issues"])
    forks_info = metrics["forks"]
    issues_info = metrics["open_issues"]

    consistency = check_consistency_rules(df)
    neg_count = consistency["open_issues_non_negative"]["negative_count"]

    return (
        forks_info["negatives"] >= 1
        and issues_info["negatives"] >= 1
        and neg_count >= 1
    )




def chase_pattern_test_outlier_detection_pattern():
    """
    author: chase
    reviewer:
    category: pattern test
    justification:
        The outlier detection logic uses repeated patterns in the data,
        such as "high stars + empty description" or "high forks + zero stars".
        Verifying that these patterns are correctly captured is important
        for manual inspection workflows in Seattle-Source-Ranker.

    description:
        Pattern test for detect_outlier_repos.

        We construct two synthetic repos:
        - one with very high stars and an empty description
        - one normal repo with low stars and a non-empty description

        The expected pattern is:
        - the high-star-empty-description repo should appear in the outlier
          set
        - the normal repo should NOT appear in the outlier set
    """
    from validate_repo_metrics import detect_outlier_repos

    df = pd.DataFrame(
        [
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
        ]
    )

    outliers = detect_outlier_repos(df, top_n=10)

    if outliers is None or len(outliers) == 0:
        return False

    names = set(outliers.get("name_with_owner", []))

    return (
        "test/high-star-empty-desc" in names
        and "normal/repo" not in names
    )


if __name__ == "__main__":
    print("----- Running HW3 Tests -----")
    print("Smoke test:", chase_smoke_test_json_to_csv_output())
    print("One-shot test:", chase_one_shot_test_metric_quality_single_repo())
    print("Edge test:", chase_edge_test_metric_quality_negative_and_missing())
    print("Pattern test:", chase_pattern_test_outlier_detection_pattern())
