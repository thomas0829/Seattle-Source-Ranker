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

# 🌐 **Technologies**
- Python  
- GitHub REST API  
- Paginated JSON  
- Validation pipelines  

---

# 🙌 **Acknowledgements**

Built for CSE583: Software Development for Data Scientists (University of Washington).
