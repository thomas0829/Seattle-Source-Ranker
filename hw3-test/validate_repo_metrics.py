#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_repo_metrics.py

Purpose
-------
Validate the reliability and internal consistency of GitHub-like repository
metadata fields such as:
- stars
- forks
- watchers
- open_issues
- created_at / pushed_at (activity timestamps)

What this script does:
1. Field-level quality checks (missing rate, negative values, basic stats)
2. Consistency checks (e.g., watchers ~= stars, pushed_at >= created_at)
3. Simple outlier detection (suspicious repos for manual inspection)

Expected Input Fields
---------------------
This script assumes data follows the JSON structure you provided:

{
  "name_with_owner": "altercation/solarized",
  "name": "solarized",
  "description": "...",
  "url": "...",
  "stars": 15942,
  "forks": 3489,
  "watchers": 15942,
  "language": "Vim script",
  "topics": [],
  "created_at": "2011-02-18T05:18:27Z",
  "updated_at": "2025-11-15T14:19:53Z",
  "pushed_at": "2024-07-11T19:57:30Z",
  "open_issues": 219,
  "has_issues": true,
  "owner": {
    "login": "altercation",
    "type": "User"
  }
}

This script keeps all field names **exactly** as they appear above.
"""

import argparse
import os
import sqlite3
from typing import Optional, List, Dict, Any

import json
import pandas as pd


# -----------------------------
# Data loading functions
# -----------------------------

def load_repos_from_csv(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"[INFO] Loaded {len(df)} repos from CSV.")
    return df


def load_repos_from_sqlite(sqlite_path: str, table_name: str) -> pd.DataFrame:
    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"SQLite database not found: {sqlite_path}")
    conn = sqlite3.connect(sqlite_path)
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    print(f"[INFO] Loaded {len(df)} repos from SQLite table '{table_name}'.")
    return df


def load_repos_df(
    csv_path: Optional[str] = None,
    sqlite_path: Optional[str] = None,
    table_name: str = "repos",
) -> pd.DataFrame:
    if csv_path:
        return load_repos_from_csv(csv_path)
    if sqlite_path:
        return load_repos_from_sqlite(sqlite_path, table_name)
    raise ValueError("Either --repos-csv or --repos-sqlite must be provided.")


# -----------------------------
# Metric quality evaluation
# -----------------------------

def compute_metric_quality(
    df: pd.DataFrame,
    columns: List[str],
) -> Dict[str, Dict[str, Any]]:
    """
    Compute quality metrics for each numeric field:
    - missing count + missing rate
    - number of negative values
    - min / max / mean / median
    """
    summary: Dict[str, Dict[str, Any]] = {}
    n = len(df)

    for col in columns:
        if col not in df.columns:
            print(f"[WARN] Missing field '{col}' in dataframe. Skipping.")
            continue

        s = pd.to_numeric(df[col], errors="coerce")

        missing = s.isna().sum()
        missing_rate = missing / n if n > 0 else 0.0
        negatives = (s < 0).sum()

        desc = s.describe()

        summary[col] = {
            "total": n,
            "missing": int(missing),
            "missing_rate": float(missing_rate),
            "negatives": int(negatives),
            "min": float(desc["min"]) if "min" in desc else None,
            "max": float(desc["max"]) if "max" in desc else None,
            "mean": float(desc["mean"]) if "mean" in desc else None,
            "median": float(desc["50%"]) if "50%" in desc else None,
        }

    return summary


# -----------------------------
# Consistency rules
# -----------------------------

def check_consistency_rules(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate cross-field logic:
    - watchers should usually equal stars
    - created_at <= pushed_at
    - open_issues must be non-negative
    """
    results: Dict[str, Any] = {}

    # watchers ≈ stars
    if "watchers" in df.columns and "stars" in df.columns:
        w = pd.to_numeric(df["watchers"], errors="coerce")
        s = pd.to_numeric(df["stars"], errors="coerce")

        valid = (~w.isna()) & (~s.isna())
        mismatch = (w != s) & valid

        results["watchers_vs_stars"] = {
            "valid_count": int(valid.sum()),
            "mismatch_count": int(mismatch.sum()),
            "mismatch_rate": float(mismatch.sum() / valid.sum()) if valid.sum() else 0.0,
        }
    else:
        results["watchers_vs_stars"] = {"info": "Missing fields: watchers or stars."}

    # created_at <= pushed_at
    if "created_at" in df.columns and "pushed_at" in df.columns:
        created = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
        pushed = pd.to_datetime(df["pushed_at"], errors="coerce", utc=True)

        valid = (~created.isna()) & (~pushed.isna())
        invalid = (pushed < created) & valid

        results["created_vs_pushed"] = {
            "valid_count": int(valid.sum()),
            "invalid_count": int(invalid.sum()),
            "invalid_rate": float(invalid.sum() / valid.sum()) if valid.sum() else 0.0,
        }
    else:
        results["created_vs_pushed"] = {"info": "Missing created_at or pushed_at."}

    # open_issues >= 0
    if "open_issues" in df.columns:
        issues = pd.to_numeric(df["open_issues"], errors="coerce")
        negatives = (issues < 0).sum()

        results["open_issues_non_negative"] = {
            "valid_count": int((~issues.isna()).sum()),
            "negative_count": int(negatives),
        }
    else:
        results["open_issues_non_negative"] = {"info": "Missing open_issues field."}

    return results


# -----------------------------
# Outlier detection
# -----------------------------

def detect_outlier_repos(df: pd.DataFrame, top_n: int = 100) -> pd.DataFrame:
    """
    Identify suspicious repositories for manual review.

    Example patterns:
    - Very high stars but empty description
    - High forks but zero stars
    - Extremely large open_issues count
    """
    for col in ["stars", "forks", "open_issues"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    candidates = []

    # High stars + missing description
    if "stars" in df.columns:
        high_star = df["stars"].fillna(0) >= 500
        no_desc = df["description"].fillna("").str.strip() == ""
        mask1 = high_star & no_desc
        candidates.append(df[mask1])

    # High forks but zero stars
    if "forks" in df.columns and "stars" in df.columns:
        high_forks = df["forks"].fillna(0) >= 100
        zero_stars = df["stars"].fillna(0) == 0
        candidates.append(df[high_forks & zero_stars])

    # Very large open_issues
    if "open_issues" in df.columns:
        many_issues = df["open_issues"].fillna(0) >= 1000
        candidates.append(df[many_issues])

    if not candidates:
        return pd.DataFrame()

    outliers = pd.concat(candidates).drop_duplicates()

    # Return the top N (by stars if available)
    if len(outliers) > top_n:
        if "stars" in outliers.columns:
            outliers = outliers.nlargest(top_n, "stars")
        else:
            outliers = outliers.head(top_n)

    return outliers


# -----------------------------
# Saving results
# -----------------------------

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_metrics_quality(metrics: Dict[str, Dict[str, Any]], output_dir: str) -> None:
    ensure_dir(output_dir)
    out_path = os.path.join(output_dir, "repo_metrics_quality.txt")

    lines = ["Repo Metrics Quality Summary\n", "================================\n\n"]

    for col, info in metrics.items():
        lines.append(f"[{col}]\n")
        for k, v in info.items():
            lines.append(f"{k}: {v}\n")
        lines.append("\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"[INFO] Saved metric quality report: {out_path}")


def save_consistency_results(results: Dict[str, Any], output_dir: str) -> None:
    ensure_dir(output_dir)
    out_path = os.path.join(output_dir, "repo_metrics_consistency.txt")

    lines = ["Repo Metrics Consistency Checks\n", "================================\n\n"]

    for rule, info in results.items():
        lines.append(f"[{rule}]\n")
        for k, v in info.items():
            lines.append(f"{k}: {v}\n")
        lines.append("\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"[INFO] Saved consistency check results: {out_path}")


def save_outliers(outliers_df: pd.DataFrame, output_dir: str) -> None:
    if outliers_df is None or len(outliers_df) == 0:
        print("[INFO] No obvious outliers detected under current rules.")
        return

    ensure_dir(output_dir)
    out_path = os.path.join(output_dir, "repo_metric_outliers.csv")
    outliers_df.to_csv(out_path, index=False)
    print(f"[INFO] Saved outlier list: {out_path}")


# -----------------------------
# CLI
# -----------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate reliability and consistency of repo metric fields."
    )

    parser.add_argument(
        "--repos-csv",
        type=str,
        help="Path to CSV file containing repo metadata.",
    )

    parser.add_argument(
        "--repos-sqlite",
        type=str,
        help="Path to SQLite DB containing repo metadata.",
    )

    parser.add_argument(
        "--repos-table",
        type=str,
        default="repos",
        help="Table name inside SQLite DB.",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="validation_outputs",
        help="Directory for saving validation reports.",
    )

    parser.add_argument(
        "--top-outliers",
        type=int,
        default=100,
        help="Max number of outliers to output.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 1. Load data
    df = load_repos_df(
        csv_path=args.repos_csv,
        sqlite_path=args.repos_sqlite,
        table_name=args.repos_table,
    )

    # 2. Metric quality summary
    print("\n[STEP] Checking field quality (stars / forks / watchers / open_issues)...")
    metric_cols = ["stars", "forks", "watchers", "open_issues"]
    metrics = compute_metric_quality(df, metric_cols)
    save_metrics_quality(metrics, args.output_dir)

    # 3. Logical consistency checks
    print("\n[STEP] Running consistency checks...")
    consistency = check_consistency_rules(df)
    save_consistency_results(consistency, args.output_dir)

    # 4. Outlier repos
    print("\n[STEP] Detecting outlier repositories...")
    outliers = detect_outlier_repos(df, top_n=args.top_outliers)
    save_outliers(outliers, args.output_dir)

    print("\n[DONE] Repo metric validation completed.\n")


if __name__ == "__main__":
    main()
