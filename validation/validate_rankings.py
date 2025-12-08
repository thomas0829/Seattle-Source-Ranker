#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_rankings.py

Purpose
-------
Validate the internal consistency of precomputed ranking files, such as:
- overall ranking (e.g., overall.json / overall.csv)
- python ranking (e.g., python.json / python.csv)
- frontend paginated rankings (e.g., frontend/public/pages/all/page_*.json)

What this script checks:
1. Schema checks for ranking files (required fields like score, name/name_with_owner)
2. Sorting consistency (score must be non-increasing)
3. Uniqueness of projects (no duplicate name_with_owner)
4. Optional length checks (expected number of rows)
5. Optional language sanity check for Python rankings (if 'language' exists)
6. Optional global_rank continuity check when available
"""

import argparse
import json
import os
import re
from typing import Dict, Any, Optional

import pandas as pd


# -----------------------------
# Helpers: loading ranking files
# -----------------------------

def load_ranking_file(path: str) -> pd.DataFrame:
    """
    Load a single ranking file. Supports:
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
            # Common structures: {"projects": [...]} or {"items": [...]}
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


def load_pages_dir(pages_dir: str) -> pd.DataFrame:
    """
    Load paginated frontend ranking files: page_1.json, page_2.json, ...

    Each page is expected to be a JSON list of project dicts, as produced by
    generate_frontend_data.py under frontend/public/pages/<lang>/.
    """
    if not os.path.isdir(pages_dir):
        raise FileNotFoundError(f"Pages directory not found: {pages_dir}")

    page_files = []
    for fname in os.listdir(pages_dir):
        m = re.match(r"page_(\d+)\.json$", fname)
        if m:
            page_num = int(m.group(1))
            page_files.append((page_num, os.path.join(pages_dir, fname)))

    if not page_files:
        raise RuntimeError(f"No page_*.json files found in {pages_dir}")

    page_files.sort(key=lambda x: x[0])

    all_rows = []
    for page_num, path in page_files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"{path} does not contain a JSON list of projects.")
        all_rows.extend(data)

    df = pd.DataFrame(all_rows)
    print(
        f"[INFO] Loaded {len(page_files)} page_*.json files from {pages_dir}, "
        f"total rows = {len(df)}"
    )
    return df


def normalize_schema_for_frontend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize schema so validation logic can always rely on 'name_with_owner'.

    - If 'name_with_owner' is missing but 'name' exists (frontend JSON),
      create name_with_owner from name.
    """
    df = df.copy()

    if "name_with_owner" not in df.columns and "name" in df.columns:
        df["name_with_owner"] = df["name"].astype(str)

    return df


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
      - required fields: 'score', 'name_with_owner' (or mapped from 'name')
      - score is non-increasing along the given order
      - no duplicate name_with_owner
      - optional: length matches expected_length
      - optional: for Python ranking, language sanity check if 'language' exists
      - optional: global_rank continuity when 'global_rank' column exists
    """
    df = normalize_schema_for_frontend(df)

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
    nan_count = int(scores.isna().sum())
    results["score_nan_count"] = nan_count

    if n > 1:
        diffs = scores.values[:-1] - scores.values[1:]
        # allow equal, only strictly < 0 is a violation
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

    # ---- global_rank continuity (if present) ----
    if "global_rank" in df.columns:
        ranks = pd.to_numeric(df["global_rank"], errors="coerce")
        rank_nan_count = int(ranks.isna().sum())
        results["global_rank_nan_count"] = rank_nan_count

        # sort by global_rank to check gaps & duplicates
        ranks_sorted = ranks.sort_values().reset_index(drop=True)
        duplicates = int(ranks_sorted.duplicated(keep=False).sum())

        if len(ranks_sorted) > 0:
            min_rank = int(ranks_sorted.iloc[0])
            max_rank = int(ranks_sorted.iloc[-1])
        else:
            min_rank = max_rank = 0

        expected_span = max_rank - min_rank + 1 if max_rank >= min_rank else 0
        gap_count = max(0, expected_span - len(ranks_sorted))

        results["global_rank_min"] = min_rank
        results["global_rank_max"] = max_rank
        results["global_rank_duplicates"] = duplicates
        results["global_rank_gaps"] = gap_count
        results["global_rank_continuous"] = (
            duplicates == 0 and gap_count == 0 and rank_nan_count == 0
        )
    else:
        results["global_rank_nan_count"] = None
        results["global_rank_min"] = None
        results["global_rank_max"] = None
        results["global_rank_duplicates"] = None
        results["global_rank_gaps"] = None
        results["global_rank_continuous"] = None

    # ---- Python ranking: language sanity check ----
    if python_rank and "language" in df.columns:
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
        description=(
            "Validate consistency of ranking files (overall/python/etc.). "
            "Supports single JSON/CSV or paginated frontend JSON pages."
        )
    )

    # single file mode
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

    # pagination mode (default)
    parser.add_argument(
        "--overall-pages-dir",
        type=str,
        default="frontend/public/pages/all",
        help="Directory with overall page_*.json files (default: frontend/public/pages/all).",
    )
    parser.add_argument(
        "--python-pages-dir",
        type=str,
        default="frontend/public/pages/python_pypi",
        help="Directory with Python+PyPI page_*.json files (default: frontend/public/pages/python_pypi).",
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
        default="validation/validation_outputs",
        help="Directory to save ranking validation reports.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # ---------- Overall ranking ----------
    if args.overall_ranking:
        # single file mode
        print("\n[STEP] Validating overall ranking from file...")
        df_overall = load_ranking_file(args.overall_ranking)
    else:
        # pagination mode (default)
        print("\n[STEP] Validating overall ranking from pages dir...")
        df_overall = load_pages_dir(args.overall_pages_dir)

    res_overall = validate_ranking_df(
        df_overall,
        ranking_name="overall",
        expected_length=args.expected_overall_size,
        python_rank=False,
    )
    save_ranking_results(res_overall, args.output_dir, "overall_ranking_validation.txt")

    # ---------- Python ranking ----------
    # if there is no python_pypi content，it will skip automatically
    if args.python_ranking or os.path.isdir(args.python_pages_dir):
        if args.python_ranking:
            print("\n[STEP] Validating python ranking from file...")
            df_python = load_ranking_file(args.python_ranking)
        else:
            print("\n[STEP] Validating python ranking from pages dir...")
            df_python = load_pages_dir(args.python_pages_dir)

        res_python = validate_ranking_df(
            df_python,
            ranking_name="python",
            expected_length=args.expected_python_size,
            python_rank=True,
        )
        save_ranking_results(res_python, args.output_dir, "python_ranking_validation.txt")
    else:
        print("\n[INFO] No python ranking file or pages dir found, skipping python ranking validation.")

    print("\n[DONE] Ranking validation completed.\n")


if __name__ == "__main__":
    main()
