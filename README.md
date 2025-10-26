# Seattle-Source-Ranker (SSR)

> A data-driven tool that identifies and ranks the most influential open-source projects from the Seattle area by analyzing GitHub repository metrics.

🌐 **Live Demo**: [https://thomas0829.github.io/Seattle-Source-Ranker](https://thomas0829.github.io/Seattle-Source-Ranker)

---

## 🌎 Overview

**Seattle-Source-Ranker (SSR)** is a comprehensive tool designed to discover and rank influential open-source projects where the owner/maintainer is located in the Seattle metropolitan area (including Seattle, Redmond, Bellevue, Kirkland, and surrounding Washington cities).

The tool fetches popular GitHub repositories, verifies owner locations, and calculates multi-dimensional influence scores to identify the most impactful projects from the Seattle tech community.

---

## 🧠 Motivation

The Seattle area hosts one of the world's most vibrant tech communities, with thousands of developers contributing to open-source projects. However, it's challenging to:
- Identify which projects are actually maintained by Seattle-area developers
- Measure project influence beyond simple star counts
- Understand the health and sustainability of these projects

SSR solves these problems by providing objective, multi-metric analysis of Seattle-based open-source contributions.

---

## ⚙️ Methodology

### **Influence Score Formula**

SSR uses a comprehensive scoring model that considers five key dimensions:

```
Score = 0.4 × S_norm + 0.25 × F_norm + 0.15 × W_norm + 0.10 × T_age + 0.10 × H_health
```

#### **Component Breakdown:**

| Metric | Weight | Description | Formula |
|--------|--------|-------------|---------|
| **S_norm** | 40% | **Normalized Stars** - Community popularity and visibility | stars / max_stars |
| **F_norm** | 25% | **Normalized Forks** - Community engagement and contribution level | forks / max_forks |
| **W_norm** | 15% | **Normalized Watchers** - Long-term interest and active followers | watchers / max_watchers |
| **T_age** | 10% | **Project Age Weight** - Maturity and longevity bonus | years / (years + 2) |
| **H_health** | 10% | **Health Score** - Project maintenance quality | 1 - (open_issues / (open_issues + 10)) |

#### **Why These Weights?**

- **Stars (40%)**: Primary indicator of community recognition and project popularity
- **Forks (25%)**: Shows active contribution and real-world usage
- **Watchers (15%)**: Indicates sustained interest and monitoring
- **Age (10%)**: Rewards established, proven projects
- **Health (10%)**: Ensures projects are well-maintained and actively managed

### **Location Verification**

The tool identifies Seattle-area developers by:
1. Searching GitHub's API for repositories with high star counts
2. Checking owner profiles for location data
3. Matching against Seattle-area keywords: seattle, redmond, bellevue, kirkland, washington
4. Caching results to minimize API calls

---

## 🧩 Features

- 📊 **Multi-Dimensional Ranking** – Combines stars, forks, watchers, age, and health metrics
- 🎯 **Location-Based Filtering** – Identifies projects by Seattle-area developers
- 💾 **Smart Caching** – Reduces API calls by caching owner location data
- 📈 **Progress Tracking** – Real-time progress bars for data collection
- 🔧 **Configurable Parameters** – Adjustable collection limits and search depth
- 📁 **JSON Export** – Exports ranked results for further analysis or visualization

---

## 🧰 Tech Stack

- **Python 3.8+**
- **APIs:** GitHub REST API v3
- **Libraries:** 
  - requests - HTTP API calls
  - tqdm - Progress bar visualization
  - argparse - CLI argument parsing
- **Frontend (Optional):** React app for web-based visualization

---

## 📁 Project Structure

```
Seattle-Source-Ranker/
│
├── main.py                      # Main CLI entry point with scoring logic
├── github_client.py             # GitHub API client wrapper
├── analyzer.py                  # Influence calculation and analysis
├── ranker.py                    # Repository ranking utilities
├── verifier.py                  # Location verification (simulated)
├── verifier_serpapi.py          # Location verification (SerpAPI-based)
│
├── data/                        # Generated data files
│   ├── owner_location_cache.json       # Cached owner locations
│   ├── ranked_project_local_seattle.json   # Main ranking results
│   └── ranked_multifactor.json         # Alternative ranking output
│
└── frontend/                    # React-based web interface
    ├── src/
    ├── public/
    └── package.json
```

---

## 🚀 Usage

### **Prerequisites**

1. Obtain a GitHub Personal Access Token:
   - Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
   - Generate a new token with public_repo scope
   
2. Set the token as an environment variable:
   ```bash
   export GITHUB_TOKEN='your_github_token_here'
   ```

### **Installation**

```bash
git clone https://github.com/thomas0829/Seattle-Source-Ranker.git
cd Seattle-Source-Ranker
pip install -r requirements.txt
```

### **Running the Tool**

Basic usage:
```bash
python main.py
```

With custom parameters:
```bash
python main.py --location Seattle --topk 50 --max-pages 20
```

#### **Command-Line Options:**

| Option | Default | Description |
|--------|---------|-------------|
| --location | Seattle | Target location keyword |
| --topk | 50 | Number of top repositories to collect |
| --max-pages | 20 | Maximum GitHub API pages to fetch (100 repos/page) |

### **Output**

The tool generates:
1. **Console output** - Formatted table showing top repositories
2. **JSON file** - data/ranked_project_local_seattle.json with detailed metrics
3. **Cache file** - data/owner_location_cache.json for faster subsequent runs

---

## 🔬 Example Output

```
🏆 Top repositories by Seattle-based developers:
--------------------------------------------
Repo                                    Stars  Forks    Score
--------------------------------------------
microsoft/vscode                        145000  24500    0.987
microsoft/TypeScript                     89000  11800    0.921
atom/atom                                58000   17200   0.856
dotnet/roslyn                            17500    3850   0.742
...
--------------------------------------------
```

---

## 📊 Sample Analysis Results

Based on real data collection, typical findings include:

- **Top Languages**: TypeScript, C#, Python, JavaScript
- **Common Project Types**: Developer tools, frameworks, ML libraries
- **Average Project Age**: 6-8 years for top-ranked projects
- **Health Trends**: Highly-ranked projects typically have <50 open issues relative to their size

---

## 🔮 Future Work

- Multi-language ecosystem support (npm, PyPI, Cargo for cross-platform analysis)
- Time-series tracking (monitor ranking changes over time)
- Contributor network analysis (identify collaboration patterns)
- Web dashboard (interactive visualization with charts and filters)
- Machine learning enhancement (predict project sustainability)
- Expanded geographic analysis (compare Seattle to other tech hubs)

---

## 🛠️ Development

### Running Tests
```bash
pytest tests/
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

---

## 📚 Acknowledgements

- **GitHub API** for providing comprehensive repository and user data
- **tqdm** for excellent progress bar functionality
- Inspired by the vibrant Seattle open-source community

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
