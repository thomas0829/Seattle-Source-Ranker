#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_rankings.py

Purpose
-------
Validate the internal consistency of precomputed ranking files, such as:
- overall ranking (e.g., overall.json / overall.csv)
- python ranking (e.g., python.json / python.csv)

What this script checks:
1. Schema checks for ranking files (required fields like score, name_with_owner)
2. Sorting consistency (score must be non-increasing)
3. Uniqueness of projects (no duplicate name_with_owner)
4. Optional length checks (expected number of rows)
5. Optional language sanity check for Python rankings (if 'language' exists)
"""

import argparse
import json
import os
from typing import Dict, Any, Optional

import pandas as pd


# -----------------------------
# Helpers: loading ranking files
# -----------------------------

def load_ranking_file(path: str) -> pd.DataFrame:
    """
    Load a ranking file. Supports:
    - JSON: either a list of objects or {"projects": [...]}
    - CSV: standard CSV with header
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Ranking file not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext in [".json"]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # 常见结构：{"projects": [...]} 或 {"items": [...]}
            if "projects" in data and isinstance(data["projects"], list):
                df = pd.DataFrame(data["projects"])
            elif "items" in data and isinstance(data["items"], list):
                df = pd.DataFrame(data["items"])
            else:
                raise ValueError(
                    "Unsupported JSON structure. Expected a list or a dict with 'projects'/'items' key."
                )
        else:
            raise ValueError("Unsupported JSON root type (expected list or dict).")

        print(f"[INFO] Loaded {len(df)} rows from JSON ranking file: {path}")
        return df

    elif ext in [".csv"]:
        df = pd.read_csv(path)
        print(f"[INFO] Loaded {len(df)} rows from CSV ranking file: {path}")
        return df

    else:
        raise ValueError(f"Unsupported ranking file extension: {ext}")


# -----------------------------
# Ranking validation
# -----------------------------

def validate_ranking_df(
    df: pd.DataFrame,
    ranking_name: str,
    expected_length: Optional[int] = None,
    python_rank: bool = False,
) -> Dict[str, Any]:
    """
    Validate a ranking dataframe.

    Checks:
      - required fields: 'score', 'name_with_owner'
      - score is non-increasing
      - no duplicate name_with_owner
      - optional: length matches expected_length
      - optional: for Python ranking, language sanity check if 'language' exists
    """
    results: Dict[str, Any] = {"ranking_name": ranking_name}

    # ---- schema ----
    required_fields = ["score", "name_with_owner"]
    missing = [f for f in required_fields if f not in df.columns]
    if missing:
        results["schema_ok"] = False
        results["missing_fields"] = missing
        return results
    else:
        results["schema_ok"] = True

    n = len(df)
    results["row_count"] = n

    # ---- length check ----
    if expected_length is not None:
        results["expected_length"] = expected_length
        results["length_match"] = (n == expected_length)
    else:
        results["expected_length"] = None
        results["length_match"] = None

    # ---- sorting by score (non-increasing) ----
    scores = pd.to_numeric(df["score"], errors="coerce")
    # 有 NaN 的先记下来
    nan_count = int(scores.isna().sum())
    results["score_nan_count"] = nan_count

    # 检查是否 score[i] >= score[i+1]
    if n > 1:
        diffs = scores.values[:-1] - scores.values[1:]
        # 允许 equal，只有严格小于 0 的算违反
        violation_mask = diffs < 0
        violation_count = int(violation_mask.sum())
    else:
        violation_count = 0

    results["sorting_violations"] = violation_count
    results["is_sorted_desc"] = (violation_count == 0)

    # ---- duplicate name_with_owner ----
    dup_mask = df["name_with_owner"].duplicated(keep=False)
    dup_count = int(dup_mask.sum())
    results["duplicate_projects"] = dup_count
    results["has_duplicates"] = (dup_count > 0)

    # ---- Python ranking: language sanity check ----
    if python_rank and "language" in df.columns:
        # 允许 language 为空，但统计非 Python 的比例
        lang_series = df["language"].fillna("UNKNOWN").astype(str)
        is_python = lang_series.str.lower().str.contains("python")
        non_python_count = int((~is_python).sum())
        results["python_language_field_present"] = True
        results["non_python_rows"] = non_python_count
        results["non_python_rate"] = float(non_python_count / n) if n > 0 else 0.0
    else:
        results["python_language_field_present"] = False
        results["non_python_rows"] = None
        results["non_python_rate"] = None

    return results


# -----------------------------
# Saving results
# -----------------------------

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_ranking_results(
    results: Dict[str, Any],
    output_dir: str,
    filename: str,
) -> None:
    ensure_dir(output_dir)
    out_path = os.path.join(output_dir, filename)

    lines = [f"Ranking Validation Report: {results.get('ranking_name')}\n",
             "=============================================\n\n"]

    for k, v in results.items():
        lines.append(f"{k}: {v}\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"[INFO] Saved ranking validation report: {out_path}")


# -----------------------------
# CLI
# -----------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate consistency of ranking files (overall/python/etc.)."
    )

    parser.add_argument(
        "--overall-ranking",
        type=str,
        help="Path to overall ranking file (JSON or CSV).",
    )
    parser.add_argument(
        "--python-ranking",
        type=str,
        help="Path to Python ranking file (JSON or CSV).",
    )

    parser.add_argument(
        "--expected-overall-size",
        type=int,
        default=None,
        help="Expected row count for overall ranking (optional).",
    )
    parser.add_argument(
        "--expected-python-size",
        type=int,
        default=None,
        help="Expected row count for Python ranking (optional).",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="validation_outputs",
        help="Directory to save ranking validation reports.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Overall ranking
    if args.overall_ranking:
        print("\n[STEP] Validating overall ranking...")
        df_overall = load_ranking_file(args.overall_ranking)
        res_overall = validate_ranking_df(
            df_overall,
            ranking_name="overall",
            expected_length=args.expected_overall_size,
            python_rank=False,
        )
        save_ranking_results(res_overall, args.output_dir, "overall_ranking_validation.txt")
    else:
        print("[INFO] No --overall-ranking provided, skipping overall ranking validation.")

    # Python ranking
    if args.python_ranking:
        print("\n[STEP] Validating python ranking...")
        df_python = load_ranking_file(args.python_ranking)
        res_python = validate_ranking_df(
            df_python,
            ranking_name="python",
            expected_length=args.expected_python_size,
            python_rank=True,
        )
        save_ranking_results(res_python, args.output_dir, "python_ranking_validation.txt")
    else:
        print("[INFO] No --python-ranking provided, skipping python ranking validation.")

    print("\n[DONE] Ranking validation completed.\n")


if __name__ == "__main__":
    main()
