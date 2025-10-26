# Seattle-Source-Ranker (SSR)# Seattle-Source-Ranker (SSR)# Seattle-Source-Ranker (SSR)



> A data-driven tool that identifies and ranks the most influential open-source projects from the Seattle area by analyzing GitHub repository metrics.



---> A data-driven tool that identifies and ranks the most influential open-source projects from the Seattle area by analyzing GitHub repository metrics.> Tool that analyzes GitHub and PyPI data to identify and rank the most influential open-source projects in Seattle, measuring both community reputation and real-world adoption.



## 🌎 Overview



**Seattle-Source-Ranker (SSR)** is a comprehensive tool designed to discover and rank influential open-source projects where the owner/maintainer is located in the Seattle metropolitan area (including Seattle, Redmond, Bellevue, Kirkland, and surrounding Washington cities).------



The tool fetches popular GitHub repositories, verifies owner locations, and calculates multi-dimensional influence scores to identify the most impactful projects from the Seattle tech community.



---## 🌎 Overview## 🌎 Overview



## 🧠 Motivation



The Seattle area hosts one of the world's most vibrant tech communities, with thousands of developers contributing to open-source projects. However, it's challenging to:**Seattle-Source-Ranker (SSR)** is a comprehensive tool designed to discover and rank influential open-source projects where the owner/maintainer is located in the Seattle metropolitan area (including Seattle, Redmond, Bellevue, Kirkland, and surrounding Washington cities).**Seattle-Source-Ranker (SSR)** is a data-driven tool that identifies and ranks the most influential open-source software projects in the Seattle area.  

- Identify which projects are actually maintained by Seattle-area developers

- Measure project influence beyond simple star countsIt integrates data from **GitHub** and **PyPI** APIs to measure both **community reputation** (e.g., stars, forks, contributors) and **real-world adoption** (e.g., downloads).  

- Understand the health and sustainability of these projects

The tool fetches popular GitHub repositories, verifies owner locations, and calculates multi-dimensional influence scores to identify the most impactful projects from the Seattle tech community.

SSR solves these problems by providing objective, multi-metric analysis of Seattle-based open-source contributions.

This project helps developers, students, and organizations explore the Seattle tech ecosystem through objective metrics and trend analysis.

---

---

## ⚙️ Methodology

---

### **Influence Score Formula**

## 🧠 Motivation

SSR uses a comprehensive scoring model that considers five key dimensions:

## 🧠 Motivation

```

Score = 0.4 × S_norm + 0.25 × F_norm + 0.15 × W_norm + 0.10 × T_age + 0.10 × H_healthThe Seattle area hosts one of the world's most vibrant tech communities, with thousands of developers contributing to open-source projects. However, it's challenging to:

```

- Identify which projects are actually maintained by Seattle-area developersThe open-source community in Seattle is large and dynamic, but it’s hard to know **which projects truly matter**.  

#### **Component Breakdown:**

- Measure project influence beyond simple star countsSSR aims to solve this by:

| Metric | Weight | Description | Formula |

|--------|--------|-------------|---------|- Understand the health and sustainability of these projects- Quantifying project influence through measurable metrics  

| **S_norm** | 40% | **Normalized Stars** - Community popularity and visibility | `stars / max_stars` |

| **F_norm** | 25% | **Normalized Forks** - Community engagement and contribution level | `forks / max_forks` |- Providing insights into growth trends and ecosystem health  

| **W_norm** | 15% | **Normalized Watchers** - Long-term interest and active followers | `watchers / max_watchers` |

| **T_age** | 10% | **Project Age Weight** - Maturity and longevity bonus | `years / (years + 2)` |SSR solves these problems by providing objective, multi-metric analysis of Seattle-based open-source contributions.- Enabling comparisons across projects, languages, and time  

| **H_health** | 10% | **Health Score** - Project maintenance quality | `1 - (open_issues / (open_issues + 10))` |



#### **Why These Weights?**

------

- **Stars (40%)**: Primary indicator of community recognition and project popularity

- **Forks (25%)**: Shows active contribution and real-world usage

- **Watchers (15%)**: Indicates sustained interest and monitoring

- **Age (10%)**: Rewards established, proven projects## ⚙️ Methodology## ⚙️ Methodology

- **Health (10%)**: Ensures projects are well-maintained and actively managed



### **Location Verification**

### **Influence Score Formula**SSR uses a **two-dimensional influence model** combining social and usage signals:

The tool identifies Seattle-area developers by:

1. Searching GitHub's API for repositories with high star counts

2. Checking owner profiles for location data

3. Matching against Seattle-area keywords: `seattle`, `redmond`, `bellevue`, `kirkland`, `washington`SSR uses a comprehensive scoring model that considers five key dimensions:| Source | Focus | Example Metrics |

4. Caching results to minimize API calls

|--------|--------|----------------|

---

```| **GitHub API** | Community influence | Stars, forks, contributors, commits |

## 🧩 Features

Score = 0.4 × S_norm + 0.25 × F_norm + 0.15 × W_norm + 0.10 × T_age + 0.10 × H_health| **PyPI API** | Real-world usage | Package downloads |

- 📊 **Multi-Dimensional Ranking** – Combines stars, forks, watchers, age, and health metrics

- 🎯 **Location-Based Filtering** – Identifies projects by Seattle-area developers```

- 💾 **Smart Caching** – Reduces API calls by caching owner location data

- 📈 **Progress Tracking** – Real-time progress bars for data collectionThese metrics are combined into an **Influence Score**, representing both visibility and adoption.

- 🔧 **Configurable Parameters** – Adjustable collection limits and search depth

- 📁 **JSON Export** – Exports ranked results for further analysis or visualization#### **Component Breakdown:**



------



## 🧰 Tech Stack| Metric | Weight | Description | Formula |



- **Python 3.8+**|--------|--------|-------------|---------|## 🧩 Features

- **APIs:** GitHub REST API v3

- **Libraries:** | **S_norm** | 40% | **Normalized Stars** - Community popularity and visibility | `stars / max_stars` |

  - `requests` - HTTP API calls

  - `tqdm` - Progress bar visualization| **F_norm** | 25% | **Normalized Forks** - Community engagement and contribution level | `forks / max_forks` |- 📊 **Influence Ranking** – Ranks projects by combined GitHub and PyPI metrics  

  - `argparse` - CLI argument parsing

- **Frontend (Optional):** React app for web-based visualization| **W_norm** | 15% | **Normalized Watchers** - Long-term interest and active followers | `watchers / max_watchers` |- 🔍 **Cross-language Analysis** – Designed to extend beyond Python (JavaScript, Java, Rust, etc.)  



---| **T_age** | 10% | **Project Age Weight** - Maturity and longevity bonus | `years / (years + 2)` |- 🧮 **Configurable Weights** – Define how much each metric contributes to the overall influence score  



## 📁 Project Structure| **H_health** | 10% | **Health Score** - Project maintenance quality | `1 - (open_issues / (open_issues + 10))` |- 📈 **Trend Analysis** – Track star growth rate, fork trends, and contributor activity over time  



```- 💡 **Insight Summaries** – Identify shared traits among top influential projects  

Seattle-Source-Ranker/

│#### **Why These Weights?**

├── main.py                      # Main CLI entry point with scoring logic

├── github_client.py             # GitHub API client wrapper---

├── analyzer.py                  # Influence calculation and analysis

├── ranker.py                    # Repository ranking utilities- **Stars (40%)**: Primary indicator of community recognition and project popularity

├── verifier.py                  # Location verification (simulated)

├── verifier_serpapi.py          # Location verification (SerpAPI-based)- **Forks (25%)**: Shows active contribution and real-world usage## 🧰 Tech Stack

│

├── data/                        # Generated data files- **Watchers (15%)**: Indicates sustained interest and monitoring

│   ├── owner_location_cache.json       # Cached owner locations

│   ├── ranked_project_local_seattle.json   # Main ranking results- **Age (10%)**: Rewards established, proven projects- **Python 3.10+**

│   └── ranked_multifactor.json         # Alternative ranking output

│- **Health (10%)**: Ensures projects are well-maintained and actively managed- **APIs:** GitHub REST API, PyPI JSON API  

└── frontend/                    # React-based web interface

    ├── src/- **Libraries:** `requests`, `pandas`, `click`, `pytest`

    ├── public/

    └── package.json### **Location Verification**- **Future Frontend:** React + Chart.js (for visualization prototype)

```



---

The tool identifies Seattle-area developers by:---

## 🚀 Usage

1. Searching GitHub's API for repositories with high star counts

### **Prerequisites**

2. Checking owner profiles for location data## 📁 Project Structure

1. Obtain a GitHub Personal Access Token:

   - Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)3. Matching against Seattle-area keywords: `seattle`, `redmond`, `bellevue`, `kirkland`, `washington`

   - Generate a new token with `public_repo` scope

   4. Caching results to minimize API calls```

2. Set the token as an environment variable:

   ```bashseattle-source-ranker/

   export GITHUB_TOKEN='your_github_token_here'

   ```---│



### **Installation**├── main.py              # CLI entry point



```bash## 🧩 Features├── github_client.py     # Handles GitHub API requests

git clone https://github.com/thomas0829/Seattle-Source-Ranker.git

cd Seattle-Source-Ranker├── pypi_client.py       # Handles PyPI API requests

pip install -r requirements.txt  # Install dependencies

```- 📊 **Multi-Dimensional Ranking** – Combines stars, forks, watchers, age, and health metrics├── analyzer.py          # Combines and processes data, computes influence



### **Running the Tool**- 🎯 **Location-Based Filtering** – Identifies projects by Seattle-area developers├── tests/               # Unit tests



Basic usage:- 💾 **Smart Caching** – Reduces API calls by caching owner location data└── README.md            # Project documentation

```bash

python main.py- 📈 **Progress Tracking** – Real-time progress bars for data collection```

```

- 🔧 **Configurable Parameters** – Adjustable collection limits and search depth

With custom parameters:

```bash- 📁 **JSON Export** – Exports ranked results for further analysis or visualization---

python main.py --location Seattle --topk 50 --max-pages 20

```



#### **Command-Line Options:**---## 🚀 Usage



| Option | Default | Description |

|--------|---------|-------------|

| `--location` | `Seattle` | Target location keyword |## 🧰 Tech Stack1. Clone the repository:

| `--topk` | `50` | Number of top repositories to collect |

| `--max-pages` | `20` | Maximum GitHub API pages to fetch (100 repos/page) |   ```bash



### **Output**- **Python 3.8+**   git clone https://github.com/your-username/seattle-source-ranker.git



The tool generates:- **APIs:** GitHub REST API v3   cd seattle-source-ranker

1. **Console output** - Formatted table showing top repositories

2. **JSON file** - `data/ranked_project_local_seattle.json` with detailed metrics- **Libraries:**    ```

3. **Cache file** - `data/owner_location_cache.json` for faster subsequent runs

  - `requests` - HTTP API calls

---

  - `tqdm` - Progress bar visualization2. Install dependencies:

## 🔬 Example Output

  - `argparse` - CLI argument parsing   ```bash

```

🏆 Top repositories by Seattle-based developers:- **Frontend (Optional):** React app for web-based visualization   pip install -r requirements.txt

--------------------------------------------

Repo                                    Stars  Forks    Score   ```

--------------------------------------------

microsoft/vscode                        145000  24500    0.987---

microsoft/TypeScript                     89000  11800    0.921

atom/atom                                58000   17200   0.8563. Run the main script:

dotnet/roslyn                            17500    3850   0.742

...## 📁 Project Structure   ```bash

--------------------------------------------

```   python main.py --language python --location seattle



---```   ```



## 📊 Sample Analysis ResultsSeattle-Source-Ranker/



Based on real data collection, typical findings include:│4. View the ranked output (JSON or table format).



- **Top Languages**: TypeScript, C#, Python, JavaScript├── main.py                      # Main CLI entry point with scoring logic

- **Common Project Types**: Developer tools, frameworks, ML libraries

- **Average Project Age**: 6-8 years for top-ranked projects├── github_client.py             # GitHub API client wrapper---

- **Health Trends**: Highly-ranked projects typically have <50 open issues relative to their size

├── analyzer.py                  # Influence calculation and analysis

---

├── ranker.py                    # Repository ranking utilities## 🔬 Example Output

## 🔮 Future Work

├── verifier.py                  # Location verification (simulated)

- [ ] **Multi-language ecosystem support** (npm, PyPI, Cargo for cross-platform analysis)

- [ ] **Time-series tracking** (monitor ranking changes over time)├── verifier_serpapi.py          # Location verification (SerpAPI-based)```

- [ ] **Contributor network analysis** (identify collaboration patterns)

- [ ] **Web dashboard** (interactive visualization with charts and filters)│Rank | Project Name     | Stars | Forks | Downloads | Influence Score

- [ ] **Machine learning enhancement** (predict project sustainability)

- [ ] **Expanded geographic analysis** (compare Seattle to other tech hubs)├── data/                        # Generated data files-----|------------------|-------|--------|------------|----------------



---│   ├── owner_location_cache.json       # Cached owner locations1    | fastapi          | 60k   | 4.5k   | 5M         | 0.98



## 🛠️ Development│   ├── ranked_project_local_seattle.json   # Main ranking results2    | streamlit        | 28k   | 2.2k   | 3M         | 0.91



### Running Tests│   └── ranked_multifactor.json         # Alternative ranking output3    | aiohttp          | 14k   | 1.5k   | 2M         | 0.86

```bash

pytest tests/│```

```

└── frontend/                    # React-based web interface

### Frontend Development

```bash    ├── src/---

cd frontend

npm install    ├── public/

npm start

```    └── package.json## 🔮 Future Work



---```



## 📚 Acknowledgements- Add **multi-language ecosystem support** (npm, Maven, Cargo)



- **GitHub API** for providing comprehensive repository and user data---- Introduce **weighted scoring configuration** for transparency

- **tqdm** for excellent progress bar functionality

- Inspired by the vibrant Seattle open-source community- Include **time-series visualization** for growth trends



---## 🚀 Usage- Generate **automatic insight summaries** from ranking results



## 📄 License- Develop **web-based dashboard** for interactive exploration



This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.### **Prerequisites**


---

1. Obtain a GitHub Personal Access Token:

   - Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)## 📚 Acknowledgements

   - Generate a new token with `public_repo` scope

   This project was developed for the **CSE 583: Data Science for Software Engineering** course.  

2. Set the token as an environment variable:APIs and data courtesy of **GitHub** and **PyPI**.

   ```bash
   export GITHUB_TOKEN='your_github_token_here'
   ```

### **Installation**

```bash
git clone https://github.com/thomas0829/Seattle-Source-Ranker.git
cd Seattle-Source-Ranker
pip install -r requirements.txt  # Install dependencies
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
| `--location` | `Seattle` | Target location keyword |
| `--topk` | `50` | Number of top repositories to collect |
| `--max-pages` | `20` | Maximum GitHub API pages to fetch (100 repos/page) |

### **Output**

The tool generates:
1. **Console output** - Formatted table showing top repositories
2. **JSON file** - `data/ranked_project_local_seattle.json` with detailed metrics
3. **Cache file** - `data/owner_location_cache.json` for faster subsequent runs

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

- [ ] **Multi-language ecosystem support** (npm, PyPI, Cargo for cross-platform analysis)
- [ ] **Time-series tracking** (monitor ranking changes over time)
- [ ] **Contributor network analysis** (identify collaboration patterns)
- [ ] **Web dashboard** (interactive visualization with charts and filters)
- [ ] **Machine learning enhancement** (predict project sustainability)
- [ ] **Expanded geographic analysis** (compare Seattle to other tech hubs)

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
