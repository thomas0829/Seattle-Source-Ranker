# Validation Suite

This directory contains validation scripts ensuring data quality and ranking integrity.

## Overview

The validation pipeline verifies:
- **Repository Metrics** - Data consistency and quality
- **Ranking Order** - Proper sorting and continuity
- **Data Integrity** - No duplicates or missing values

## Running Validation

```bash
# From project root
cd validation

# Convert JSON to CSV
python json_to_csv.py

# Validate repository metrics
python validate_repo_metrics.py

# Validate rankings
python validate_rankings.py
```

## Validation Results

| Category | Status |
|----------|--------|
| **Overall Ranking** | Passed - 10,000 repos, perfectly sorted |
| **Python Ranking** | Passed - 53,885 repos, all Python, sorted |
| **Repo Metrics** | Minor warnings - 0.65% timestamp anomalies (non-critical) |
| **Data Quality** | Clean - No missing or negative values |

## Scripts

- `json_to_csv.py` - Converts JSON data to CSV format
- `validate_repo_metrics.py` - Checks data consistency and quality
- `validate_rankings.py` - Validates ranking order and schema

## Manual Sampling

We manually audited 50 randomly sampled users to verify location accuracy:
- **88% matched** - GitHub location = external profile
- **12% mismatched** - Relocated users or unverifiable

This validates using GitHub location metadata as a reliable proxy for Seattle-based developers.

## Outputs

Validation results are saved to `validation_outputs/`:
- `overall_ranking_validation.txt`
- `python_ranking_validation.txt`
- `repo_metrics_consistency.txt`
- `repo_metrics_quality.txt`
- `repo_metric_outliers.csv`

## Technologies

- Python
- GitHub REST API
- Pandas for data analysis
