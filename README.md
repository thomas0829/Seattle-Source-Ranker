# Seattle-Source-Ranker (SSR)

> Tool that analyzes GitHub and PyPI data to identify and rank the most influential open-source projects in Seattle, measuring both community reputation and real-world adoption.

---

## 🌎 Overview

**Seattle-Source-Ranker (SSR)** is a data-driven tool that identifies and ranks the most influential open-source software projects in the Seattle area.  
It integrates data from **GitHub** and **PyPI** APIs to measure both **community reputation** (e.g., stars, forks, contributors) and **real-world adoption** (e.g., downloads).  

This project helps developers, students, and organizations explore the Seattle tech ecosystem through objective metrics and trend analysis.

---

## 🧠 Motivation

The open-source community in Seattle is large and dynamic, but it’s hard to know **which projects truly matter**.  
SSR aims to solve this by:
- Quantifying project influence through measurable metrics  
- Providing insights into growth trends and ecosystem health  
- Enabling comparisons across projects, languages, and time  

---

## ⚙️ Methodology

SSR uses a **two-dimensional influence model** combining social and usage signals:

| Source | Focus | Example Metrics |
|--------|--------|----------------|
| **GitHub API** | Community influence | Stars, forks, contributors, commits |
| **PyPI API** | Real-world usage | Package downloads |

These metrics are combined into an **Influence Score**, representing both visibility and adoption.

---

## 🧩 Features

- 📊 **Influence Ranking** – Ranks projects by combined GitHub and PyPI metrics  
- 🔍 **Cross-language Analysis** – Designed to extend beyond Python (JavaScript, Java, Rust, etc.)  
- 🧮 **Configurable Weights** – Define how much each metric contributes to the overall influence score  
- 📈 **Trend Analysis** – Track star growth rate, fork trends, and contributor activity over time  
- 💡 **Insight Summaries** – Identify shared traits among top influential projects  

---

## 🧰 Tech Stack

- **Python 3.10+**
- **APIs:** GitHub REST API, PyPI JSON API  
- **Libraries:** `requests`, `pandas`, `click`, `pytest`
- **Future Frontend:** React + Chart.js (for visualization prototype)

---

## 📁 Project Structure

```
seattle-source-ranker/
│
├── main.py              # CLI entry point
├── github_client.py     # Handles GitHub API requests
├── pypi_client.py       # Handles PyPI API requests
├── analyzer.py          # Combines and processes data, computes influence
├── tests/               # Unit tests
└── README.md            # Project documentation
```

---

## 🚀 Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/seattle-source-ranker.git
   cd seattle-source-ranker
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the main script:
   ```bash
   python main.py --language python --location seattle
   ```

4. View the ranked output (JSON or table format).

---

## 🔬 Example Output

```
Rank | Project Name     | Stars | Forks | Downloads | Influence Score
-----|------------------|-------|--------|------------|----------------
1    | fastapi          | 60k   | 4.5k   | 5M         | 0.98
2    | streamlit        | 28k   | 2.2k   | 3M         | 0.91
3    | aiohttp          | 14k   | 1.5k   | 2M         | 0.86
```

---

## 🔮 Future Work

- Add **multi-language ecosystem support** (npm, Maven, Cargo)
- Introduce **weighted scoring configuration** for transparency
- Include **time-series visualization** for growth trends
- Generate **automatic insight summaries** from ranking results
- Develop **web-based dashboard** for interactive exploration

---

## 📚 Acknowledgements

This project was developed for the **CSE 583: Data Science for Software Engineering** course.  
APIs and data courtesy of **GitHub** and **PyPI**.
