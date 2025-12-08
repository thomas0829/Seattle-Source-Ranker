Seattle-Source-Ranker — Validation Summary
=========================================

This document summarizes all validation procedures performed on the project’s
ranking data and raw GitHub metadata. It consolidates outputs from multiple
validation scripts to provide a clear picture of dataset correctness, ordering
consistency, and overall data quality.

----------------------------------------------------------------------
1. Overall Ranking Validation (Top 10,000 Repositories)
----------------------------------------------------------------------

The overall ranking validation ensures that the top 10,000 GitHub repositories
are correctly ordered and internally consistent.

Key results:
- Schema fully valid (schema_ok = True)
- Successfully loaded all 10,000 ranked items
- No missing or NaN score values
- Score ordering strictly correct (is_sorted_desc = True)
- No duplicate repositories
- global_rank spans cleanly from 1 to 10,000
- No rank gaps or discontinuities
- Suitable for frontend consumption

Conclusion:
The overall ranking dataset is perfectly valid and internally coherent. All
entries follow expected ordering and uniqueness constraints.

----------------------------------------------------------------------
2. Python + PyPI Ranking Validation
----------------------------------------------------------------------

This ranking is a filtered subset of GitHub repositories that include Python 
projects, with optional PyPI-based score bonuses.

Key results:
- 53,885 Python repositories included
- All entries have valid scores
- Score ordering correct across all entries
- No duplicate repositories
- All entries correctly identified as Python repositories
- global_rank is non-continuous (expected due to subset nature)
- Large global_rank gaps represent intervening non-Python repositories

Conclusion:
The Python ranking is clean, consistent, and properly filtered. All entries
adhere to ordering and type expectations. Non-continuous global ranks are valid
because this ranking represents a subset of the overall dataset.

----------------------------------------------------------------------
3. Repository Metrics Consistency Checks
----------------------------------------------------------------------

Two structural checks were performed on raw GitHub metadata:

(created_at vs pushed_at)
- 432,421 valid repositories
- 2,806 invalid entries (~0.65%), handled as low-severity warnings
- Likely caused by upstream metadata inconsistencies or unusual repo history

(open_issues non-negative)
- 100% valid
- No negative values found

Conclusion:
Repository metadata is generally well-formed. Timestamp irregularities exist but
are rare and not impactful to downstream ranking.

----------------------------------------------------------------------
4. Repository Metrics Quality Summary
----------------------------------------------------------------------

Quality statistics were generated for stars, forks, watchers, and open issues.

Key results across 432,421 repositories:
- No missing values in any metrics
- No negative values
- Metrics are statistically reasonable:
  * Stars:   min=0, max=60761, mean=6.54, median=0
  * Forks:   min=0, max=243374, mean=2.09, median=0
  * Watchers:min=0, max=1786, mean=1.29, median=1
  * Issues:  min=0, max=1523, mean=0.99, median=0

Conclusion:
All important repository metrics are structurally sound and free from errors. 
Data is suitable for use in the ranking algorithms without further cleaning.

----------------------------------------------------------------------
Final Conclusion
----------------------------------------------------------------------

Across all validation components—ranking integrity, duplicate detection,
sorting correctness, and raw metric health—the Seattle-Source-Ranker dataset
is clean, reliable, and production-ready.

The computed overall and Python rankings show correct ordering, no duplication,
and robust schema consistency. All supporting metadata is sufficiently clean for
use in scoring and frontend display.

This validation confirms that the dataset can be safely used for further
analysis and presentation.
