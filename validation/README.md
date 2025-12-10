# 📘 **Validation Overview**

Seattle-Source-Ranker provides a complete validation pipeline ensuring that all
GitHub project data and ranking outputs are structurally correct, statistically
clean, and ready for downstream analysis or frontend display.

This repository does **not** simply compute rankings — it enforces a full
multi-stage verification workflow, turning raw JSON project data into validated,
trustworthy ranking outputs.

---
---

```
🗂 **Raw Input**  
┌─────────────────────────────┐  
│ Raw Project Data            │
│ (seattle_projects.json)     │  
└───────────────┬─────────────┘  
                ↓  
📝 **Convert Format**  
┌─────────────────────────────┐  
│ JSON → CSV Conversion        │  
│ (json_to_csv.py)             │  
└───────────────┬─────────────┘  
                ↓  
🔍 **Metadata Validation**  
┌─────────────────────────────┐  
│ Repo Metrics Validation      │  
│ - Consistency Checks         │  
│ - Quality Summary            │  
│ (validate_repo_metrics.py)   │  
└───────────────┬─────────────┘  
                ↓  
🏆 **Ranking Validation**  
┌─────────────────────────────┐  
│ Ranking Validation           │  
│ - Overall ranking            │  
│ - Python+PyPI ranking        │  
│ (validate_rankings.py)       │  
└───────────────┬─────────────┘  
                ↓  
📤 **Final Outputs**  
┌─────────────────────────────┐  
│ Validation Outputs           │  
│ - overall_ranking_validation │  
│ - python_ranking_validation  │  
│ - repo_metrics_consistency   │  
│ - repo_metrics_quality       │  
│ - repo_metric_outliers.csv   │
│ (validation_outputs/)        │  
└─────────────────────────────┘
```
---

# 🏆 **Ranking Outputs**

### **1. Overall Ranking**
- Top 10,000 GitHub projects scored and globally ranked  
- Uses enhanced SSR scoring (stars, forks, maturity, activity, health)

### **2. Python + PyPI Ranking**
- Python repositories only  
- Additional bonus for PyPI packages  
- Used for Python-specific leaderboard

Paginated outputs:

```
frontend/public/pages/all/page_*.json
frontend/public/pages/python_pypi/page_*.json
```

---

# 🛡️ **Validation Suite**

Validation scripts located in:

```
validation/
```

---

## 🧪 **Validation Summary (High-Visibility Table)**

| Category | Purpose | Findings | Status |
|---------|---------|----------|--------|
| **Overall Ranking** | Validate sorting, ranking continuity, duplication | 10,000 repos, perfectly sorted, continuous rank, no duplicates | 🟢 **Passed** |
| **Python Ranking** | Verify Python-only filtering + PyPI adjustments | 53,885 repos, all Python, sorted, no duplicates, expected rank gaps | 🟢 **Passed** |
| **Repo Metrics Consistency** | created_at vs pushed_at, non-negative metrics | 0.65% timestamp anomalies (non-critical), open_issues valid | 🟡 **Minor warnings** |
| **Metric Quality** | Check missing/invalid values, distribution | No missing or negative fields, distributions reasonable | 🟢 **Clean** |

---

## 🎯 **Final Validation Conclusion**

All datasets are:

- ✔ Correctly ordered  
- ✔ Free of duplicates  
- ✔ Structurally sound  
- ✔ Backed by high-integrity data  
- ✔ Ready for frontend and analysis  

Full validation summary:

```
Seattle-Source-Ranker — Validation Summa.md
```

---

# 🧩 **Key Scripts**

| File | Description |
|------|-------------|
| `json_to_csv.py` | Utility converter |
| `validate_repo_metrics.py` | Checks raw metadata consistency and quality|
| `validate_rankings.py` | Validates ranking order, schema consistency, duplicates |


---

# 🚀 **How to Run Validation**

From project root:
### Validate repo metrics consistency & Validate repo metrics quality
```bash
python json_to_csv.py
python validate_repo_metrics.py
```

### Validate Overall Ranking & Validate Python Ranking
```bash
python validate_rankings.py
```

Outputs:

```
validation/validation_outputs/
```

---

# 📂 **Project Structure**

```
Seattle-Source-Ranker/
│
├── ……
├── validation/
│   ├── json_to_csv.py
│   ├── validate_repo_metrics.py
│   ├── validate_rankings.py
│   ├── if_seattle_Random_manual_sampling.xlsx
│   ├── README.md
│   └── validation_outputs/
│       ├── overall_ranking_validation.txt
│       ├── python_ranking_validation.txt
│       ├── repo_metrics_consistency.txt
│       ├── repo_metrics_quality.txt
│       ├── repo_metric_outliers.csv
│       └── Seattle-Source-Ranker — Validation Summa.md 
└── data/
```

---

# 📊 Manual Random Sampling Validation (Human-Audited Location Check)

To evaluate the real-world reliability of GitHub location metadata, we manually audited **50 randomly sampled GitHub users** and compared:

- GitHub profile location  
- External profiles (LinkedIn, personal websites, company pages)  
- Public employment / bio / project metadata  

This cross-verification helps confirm whether GitHub location data is a valid proxy for real user location — an essential assumption for this project.

---

## 📈 Sampling Results (50 Users)

| Category | Count | Percentage |
|----------|--------|------------|
| **Matched (GitHub location = external profile)** | **44** | **88%** |
| **Mismatched (conflicts or unverifiable)** | **6** | **12%** |

---

## 🥧 Visual Breakdown

```
Matched      ████████████████████████████████████████  44 (88%)
Mismatched   ████                                      6 (12%)
```

---

## 🔍 Interpretation of Mismatches (6 Users)

The 6 mismatches typically fell into the following categories:

### ❗ 1. Users who relocated but never updated GitHub  
- GitHub still shows “Seattle”  
- LinkedIn lists a new city (e.g., SF / NYC / remote)


### ❗ 2. Missing external references  
- No LinkedIn / personal website  
- No self-reported external location  
- Not strictly a mismatch, but unverifiable

---

## 📌 Meaning for Our Project

An **88% match rate** demonstrates:

### ✔ GitHub user location is generally reliable  
### ✔ Filtering Seattle users based on GitHub metadata is statistically supported  
### ✔ The observed mismatch rate is reasonable in public datasets  
### ✔ Manual sampling strengthens dataset credibility  

---

## 📁 Sampling File

```
validation/if_seattle_Random_manual_sampling.xlsx
```

Contains fields such as:

- GitHub username  
- GitHub location field  
- External profile URL  
- Match? (Yes / No)  
- Notes on mismatch reasoning  

---

## 🧾 Conclusion

This manual audit adds a human-verification layer on top of automated validation.

**Even with a 12% mismatch rate, our sampling strongly supports the use of GitHub location as a meaningful proxy for identifying Seattle-based developers.**

This provides additional real-world endorsement for the correctness and robustness of our dataset filtering logic.


---

# 🌐 **Technologies**
- Python  
- GitHub REST API  
- Paginated JSON  
- Validation pipelines  

---

# 🙌 **Acknowledgements**

Built for CSE583: Software Development for Data Scientists (University of Washington).
