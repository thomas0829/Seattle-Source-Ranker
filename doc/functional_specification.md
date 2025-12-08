# Functional Specification: Seattle Source Ranker

## 1. Background

### Problem Statement
Seattle has a thriving open-source community with thousands of developers contributing to projects across various technologies. However, there is no centralized, data-driven platform to discover, analyze, and rank these local projects. This creates several challenges:

- **Talent Discovery**: Recruiters struggle to identify skilled developers through their open-source contributions
- **Project Discovery**: Developers cannot easily find high-quality local projects to contribute to or learn from
- **Community Visibility**: The Seattle tech ecosystem lacks a unified view of its open-source landscape
- **Quality Assessment**: No standardized metric exists to evaluate project quality beyond simple star counts

### Solution
Seattle Source Ranker addresses these challenges by:
1. **Automated Data Collection**: Systematically collecting data from ~28K+ Seattle-based GitHub users
2. **Intelligent Ranking**: Using a multi-factor SSR (Seattle Source Ranker) algorithm that considers popularity, maintenance, and project health
3. **Interactive Visualization**: Providing a web-based interface for exploring projects by language, PyPI status, and other criteria
4. **Daily Updates**: Maintaining fresh data through automated collection and deployment
5. **One-Command Setup**: Local pipeline execution via `./run_local.sh` for development and testing

### Project Goals
- Provide a comprehensive, searchable database of Seattle open-source projects
- Rank projects using quality metrics beyond simple popularity
- Support multiple user personas from recruiters to students
- Maintain data freshness through automated daily updates
- Serve as both a Python library (installable from source) and web-based exploration tool

---

## 2. User Profile

### Primary Users

#### Technical Recruiters (e.g., Sarah, Jessica)
**Background**: Work at tech companies or staffing agencies in Seattle area  
**Technical Knowledge**: Moderate - familiar with GitHub, programming languages, and project metrics  
**Computing Skills**: Web browsing, filtering/searching interfaces, basic data interpretation  
**Goals**:
- Discover developers with strong open-source portfolios
- Filter projects by language and activity level
- Assess candidate technical skills through contribution patterns

#### Software Engineers (e.g., Alex, Kevin)
**Background**: Professional developers seeking to contribute or learn  
**Technical Knowledge**: High - experienced with version control, coding standards, and software architecture  
**Computing Skills**: Can use Python libraries, read documentation, and analyze code quality  
**Goals**:
- Find high-quality projects for contribution
- Discover libraries for integration into their work
- Learn from real-world code examples
- Network with local developers

#### Students & Researchers (e.g., Muwen, Emily, Michael)
**Background**: Academic environment, learning programming or conducting research  
**Technical Knowledge**: Basic to moderate - comfortable with programming but still learning  
**Computing Skills**: Can run Python scripts, read documentation, and perform data analysis  
**Goals**:
- Learn real-world coding practices
- Find beginner-friendly projects for contributions
- Conduct research on developer ecosystems
- Build portfolios for career development

#### Community Organizers & Journalists (e.g., Lisa, Maria)
**Background**: Focus on tech community events and coverage  
**Technical Knowledge**: Basic - understand GitHub terminology but not deeply technical  
**Computing Skills**: Web browsing, understanding visualizations, basic data interpretation  
**Goals**:
- Identify trending projects and influential developers
- Find speakers for events
- Track community growth and activity
- Write informed articles about local tech scene

### Secondary Users

#### Business Analysts (e.g., Rachel, David)
**Background**: Technical due diligence, team management, or consulting  
**Technical Knowledge**: Moderate to high - can assess technical capability  
**Computing Skills**: Data analysis, reporting, developer evaluation  
**Goals**:
- Evaluate technical teams for acquisitions
- Track team members' skill development
- Assess project viability for business decisions

---

## 3. Data Sources

### 3.1 GitHub API (Primary Source)

**Type**: REST API v3 and GraphQL API v4  
**Access**: Personal Access Tokens with `read:org` scope  
**Rate Limits**: 5K requests/hour per token (~30K/hour with 6 tokens)

**Three-Stage Collection Strategy**:

**Stage 1: User Discovery (GraphQL Search API)**
- **Purpose**: Fast collection of Seattle-based user accounts
- **Why GraphQL**: Search API is extremely fast for user discovery (~76 optimized location queries)
- **Limitation**: GraphQL bulk queries for repository details are unstable and error-prone
- **Data Collected**: 
  - User login names, account types (User/Organization)
  - Location filters: Seattle, Redmond, Bellevue, etc.
  - Quality filters: follower count, repository count thresholds

**Stage 2: Repository Collection (REST API)**
- **Purpose**: Stable, reliable collection of repository metadata
- **Why REST**: More stable than GraphQL for bulk operations, less prone to errors
- **Limitation**: `watchers` field returns `stargazers_count` (incorrect), cannot detect empty/private repos accurately
- **Data Collected**:
  - Repository name, description, owner
  - Stars, forks, watchers (incorrect value - actually returns stars)
  - Open issues count
  - Primary programming language
  - Topics/tags
  - Creation date, last push date
  - Homepage URL, repository URL

**Stage 3: Secondary Validation (GraphQL API + HEAD requests)**
- **Purpose**: Fix REST API limitations and validate repository accessibility
- **Why GraphQL Again**: Provides accurate `watchers` field (real `subscribers_count`, not stars)
- **Why HEAD Requests**: Detect deleted/private/blocked repositories (HTTP 4xx errors)
- **Corrections Made**:
  - Replace incorrect watchers with real subscribers count via GraphQL
  - Remove inaccessible repositories (deleted, private, legally blocked)
  - Recalculate aggregate statistics with validated data

**Data Characteristics**:
- **Granularity**: Individual repository level
- **Freshness**: Updated daily via automated collection
- **Volume**: ~430K+ projects from ~28K+ users
- **Completeness**: Full metadata for public repositories

### 3.2 PyPI (Python Package Index)

**Type**: JSON API and Simple Index HTML  
**Access**: Public API, no authentication required

**Data Collected**:
- Complete list of published package names (~700K+ packages)
- Top 15K most-downloaded packages (for global impact detection)
- Used for offline matching against GitHub projects

**Data Characteristics**:
- **Granularity**: Package name level
- **Freshness**: Package index cached for ~7 days, refreshed automatically
- **Usage**: Binary classification (on PyPI / not on PyPI, Top 15K / not Top 15K)
- **Volume**: ~700K+ total packages, Top 15K most-downloaded packages
- **Matching Strategy**: Multiple algorithms including:
  - Direct name matching (case-insensitive)
  - Prefix removal (python-, py-, django-, flask-, pytest-)
  - Underscore/hyphen normalization
  - Manual mappings for edge cases (e.g., beautifulsoup → beautifulsoup4)
  - Signal verification (topics, description keywords)

### 3.3 Data Integration

**Join Strategy**:
Projects are matched between GitHub and PyPI using:
1. **Primary**: Repository name matching with normalization
2. **Validation**: Topic checking (pypi, python-package, pip)
3. **Filtering**: Generic name exclusion (awesome-, tutorial-, etc.)

**Data Flow**:
```
GitHub API → User Collection (GraphQL) → Repository Collection (REST + Celery) → 
Secondary Validation & Enrichment (scripts/secondary_update.py):
  - Validate repository accessibility (HEAD requests)
  - Remove deleted/private/blocked repositories (HTTP 4xx errors)
  - Update watchers with real subscribers_count (not stars)
  - Recalculate aggregate statistics
  - 8 workers × 2 concurrency = 16 parallel validations
  - Processing time: ~30-40 minutes (vs ~5 hours single-threaded) →
PyPI Matching (Offline) → Top PyPI Matching → SSR Scoring → 
Frontend Data Generation → Web Interface Deployment
```

**Data Quality**:
- **Coverage**: ~28K+ Seattle users, ~430K+ projects, ~2.8M+ total stars
- **Accuracy**: ~2% of repositories removed during secondary validation (deleted/private/blocked)
- **Watchers Validation**: Real subscribers count via REST API (not stars field)
- **Repository Accessibility**: All projects verified as accessible before deployment
- **Precision**: ~100% for PyPI matching (zero false positives via strict matching)
- **Detection Rates**: 
  - PyPI packages: ~2-3% of Python projects (~1K+ packages)
  - Top 15k Global: ~0.05-0.1% of Python projects (~30 packages)
- **Update Frequency**: Daily automated collection at midnight Seattle time (~08:00 UTC)

---

## 4. Use Cases

### Use Case 1: Technical Recruiter Discovering Local Talent

**Objective**: Jessica, a technical recruiter at Amazon, wants to find senior Python developers in Seattle with strong open-source contributions for an upcoming role.

**User Interactions**:

1. **Access System**
   - Jessica visits https://thomas0829.github.io/Seattle-Source-Ranker/
   - Sees homepage with total statistics (~430K+ projects, ~2.8M+ stars, overview cards)

2. **Navigate to Python Rankings**
   - Clicks "Python Rankings" navigation link from home page
   - Views page showing ~54K Python projects from Seattle
   - Sees dedicated Python page with PyPI bonus information

3. **Filter and Search**
   - Uses search bar with real-time autocomplete suggestions
   - System provides owner suggestions (👤 icon) and topic suggestions (🏷️ icon)
   - Keyboard navigation: arrow keys to select, Enter to apply
   - Can filter by owner name or search by repository name
   - Search query persisted in URL for sharing

4. **Browse PyPI Projects**
   - Filters results to projects with PyPI badges
   - Rainbow badge: Regular PyPI packages (~1K+ projects, +5% bonus)
   - Gold-purple luxury badge: Top 15k Global packages (~30 projects, +15.5% bonus)
   - Badges animate with gradient effects

4. **Review Project Details**
   - Browses paginated results (~50 projects per page)
   - For each project, sees:
     * SSR Score with visualization bar (e.g., 843,215 points)
     * Stars, Forks, Watchers counts
     * Last activity date (formatted as relative time)
     * PyPI badges: rainbow (regular) or luxury gold-purple (Top 15k)
     * Language tag and topic chips
     * Hover tooltip with additional details
     * Direct links to GitHub repository and owner profile
   - Can jump to specific page using page input box
   - Can navigate using Previous/Next buttons or page numbers

5. **Use Advanced Features**
   - Multi-language filtering on Overall Rankings page
   - Toggle "Show All" / "Show Selected" languages
   - URL state preservation (can bookmark or share filtered views)
   - Browser back/forward navigation maintains search state
   - Scroll position restored on page refresh (F5)
   - Row animations on search/filter changes

6. **Identify Candidates**
   - Clicks on promising project owners' GitHub profiles
   - Reviews their public contributions
   - Records candidate information for outreach

**Expected Outcome**: Jessica successfully identifies 5-10 high-quality Python developers with active PyPI packages, especially those in the Top 15k global packages, indicating production-level Python expertise and global impact. The SSR score helps her prioritize candidates by combining popularity with code quality and maintenance activity. The search and filtering features allow her to quickly narrow down candidates matching specific criteria.

---

### Use Case 2: Software Engineer Using Package as Library

**Objective**: Alex, a software engineer, wants to programmatically analyze Seattle projects for a data visualization project at his company.

**User Interactions**:

1. **Clone and Install from Source**
   ```bash
   git clone https://github.com/thomas0829/Seattle-Source-Ranker.git
   cd Seattle-Source-Ranker
   pip install -e .
   ```

2. **Import and Use Scoring Module**
   ```python
   from seattle_source_ranker.scoring import calculate_github_score
   
   # Sample project data from internal database
   project = {
       'stars': 1500,
       'forks': 200,
       'watchers': 80,
       'open_issues': 25,
       'created_at': '2020-06-15T00:00:00Z',
       'pushed_at': '2024-11-20T10:30:00Z'
   }
   
   score = calculate_github_score(project)
   print(f"Project SSR Score: {score:.2f}")  # Output: 7245.32
   ```

3. **Use PyPI Checker**
   ```python
   from seattle_source_ranker.pypi import PyPIChecker
   
   checker = PyPIChecker()
   
   # Check individual project
   project = {
       'name': 'requests', 
       'language': 'Python', 
       'topics': ['http', 'python'],
       'description': 'Python HTTP for Humans'
   }
   
   is_on_pypi = checker.check_project(project)
   print(f"On PyPI: {is_on_pypi}")  # Output: On PyPI: True
   ```

4. **Manage GitHub Tokens**
   ```python
   from seattle_source_ranker.tokens import get_token_manager
   
   tm = get_token_manager()  # Singleton instance
   token = tm.get_token()  # Gets best available token
   
   # Check all tokens
   for i, token in enumerate(tm.get_all_tokens(), 1):
       info = tm._check_token_rate_limit(token)
       print(f"Token {i}: {info['remaining']}/{info['limit']}")
   ```

5. **Build Custom Analysis**
   - Alex uses these components to build an internal dashboard
   - Tracks his team's open-source activity
   - Identifies potential libraries for integration

**Expected Outcome**: Alex successfully integrates Seattle Source Ranker as a library into his company's internal tools, using the SSR scoring algorithm to evaluate project quality and PyPI checker to validate package distribution status.

---

### Use Case 3: Computer Science Student Learning and Contributing

**Objective**: Michael, a bootcamp student at Code Fellows, wants to find beginner-friendly Python projects in Seattle to make his first open-source contribution.

**User Interactions**:

1. **Access Website**
   - Michael visits the Seattle Source Ranker homepage
   - Reads about the SSR scoring methodology on the "Scoring" page
   - Understands that recent activity (activity_factor) indicates maintainer responsiveness

2. **Filter for Suitable Projects**
   - Navigates to Python Rankings page
   - Searches for "tutorial" or "beginner" in search bar
   - Sorts by "Recent Activity" to find actively maintained projects
   - Looks for projects with moderate stars (500-5000) indicating established but not overwhelming projects

3. **Review Project Details**
   - Examines health factor scores (lower issue ratios indicate well-maintained projects)
   - Checks last push date to confirm active maintenance
   - Reviews topics to find projects matching his interests (web development, data analysis)

4. **Select Target Project**
   - Finds a Flask web application project with:
     * SSR Score: 6,200 (good quality)
     * 1,200 stars (established community)
     * Last push: 3 days ago (active)
     * Health factor: 0.9 (well-maintained)
     * Topics: [flask, web, beginner-friendly]

5. **Take Action**
   - Clicks through to GitHub repository
   - Reviews CONTRIBUTING.md guidelines
   - Checks open issues labeled "good first issue"
   - Makes first contribution

**Expected Outcome**: Michael successfully identifies an approachable project with active maintainers in Seattle, makes his first contribution, and adds it to his portfolio. The SSR scoring system helped him avoid abandoned projects and overly complex codebases.

---

## 5. System Interactions Summary

### Web Interface Workflow
```
User → Home Page → [Overall Rankings | Python Rankings | Scoring | Validation] → 
Search/Filter → Browse Results → View Details → Click GitHub Links
```

### Additional Web Features
- **URL State Management**: All filters, search, and pagination preserved in URL
- **Session Storage**: Scroll position maintained across page refreshes
- **Responsive Design**: Mobile and desktop optimized layouts
- **Accessibility**: Keyboard navigation, semantic HTML, ARIA labels
- **Performance**: Page caching, lazy loading, debounced search

### Library Usage Workflow
```
pip install → Import modules → Call functions → Integrate into application
```

### Local Development Workflow
```bash
# One-command pipeline execution
./run_local.sh          # Test mode (30 users)
./run_local.sh --full   # Full collection (all users)
```

**Automated Steps**:
1. Environment setup (conda/pip auto-detection and installation)
2. Token validation (checks all GitHub tokens in `.env.tokens`)
3. Redis server check/start
4. Data collection (GraphQL + REST with Celery workers)
5. PyPI official index update (~700K packages)
6. Secondary validation (repository accessibility, watchers update)
7. PyPI detection and matching
8. Top PyPI rankings check and extraction (~15K packages)
9. SSR scoring calculation
10. Frontend generation and build
11. Local development server launch

### Automated Data Pipeline
System runs daily via GitHub Actions:
1. **Collection**: GraphQL (users) → REST (repositories) → Validation (accessibility check)
2. **Enrichment**: PyPI matching → SSR scoring
3. **Deployment**: Frontend generation → GitHub Pages

(See Component Specification for detailed workflow)

### Key System Behaviors
- **Real-time Search**: Debounced input (~300ms) with autocomplete suggestions for owners and topics
- **Smart Suggestions**: Pre-loaded owner indices (a-z + other) for instant autocomplete
- **Keyboard Navigation**: Arrow keys + Enter for suggestion selection
- **Pagination**: ~50 projects per page with lazy loading and page caching
- **Score Visualization**: Relative score bars based on min/max scores per language
- **Score Calculation**: SSR algorithm runs during frontend data generation (backend-only, not on-demand)
- **PyPI Detection**: Offline matching using cached package list (refreshed every ~7 days)
- **Token Rotation**: Automatic selection of best available GitHub token (highest remaining rate limit)
- **Error Handling**: Graceful fallback for rate limits, API errors, with retry logic
- **Distributed Processing**: ~8 Celery workers with ~2 concurrent tasks each (~16 parallel operations)
- **Seattle Timezone**: All timestamps in America/Los_Angeles timezone for consistency
- **URL State Preservation**: Search, filters, and page number stored in URL parameters
- **Scroll Restoration**: Session storage maintains scroll position across refreshes
- **Cache Strategy**: Page data cached in memory to avoid redundant fetches
- **Animation System**: Row animations and table flash effects on data updates

---

## 6. Non-Functional Requirements

### Performance
- Website loads in < ~2 seconds (static GitHub Pages hosting)
- Search autocomplete responds within ~200ms (debounced)
- Pagination and filtering are instant (client-side with cached data)
- Complete data collection finishes within ~60-90 minutes for ~30K users
- PyPI checking processes ~54K Python projects in < ~30 seconds (offline matching)
- Distributed workers achieve ~5-7.5× speedup over single-threaded collection
- Owner index loading: <~100ms per character group (a-z)

### Reliability  
- Daily automated updates with failure recovery and rollback protection
- ~99.9%+ uptime for static website (GitHub Pages SLA)
- Zero false positives for PyPI package detection (~100% precision)
- Automatic token rotation prevents rate limit exhaustion
- Celery task retry logic for transient failures
- Graceful degradation when PyPI data unavailable

### Usability
- Mobile-responsive design with glass morphism aesthetic
- Clear documentation in README, doc/, and examples/
- Intuitive search and filter interface with instant feedback
- Accessible to users with basic technical knowledge
- Five dedicated pages (Home, Overall Rankings, Python Rankings, Scoring, Validation)
- Keyboard shortcuts and navigation support
- Visual feedback (animations, hover effects, loading states)
- URL-based state for easy sharing and bookmarking

### Maintainability
- ~225+ passing tests with pytest (~56% overall coverage, ~94-100% core modules)
- Code quality score ≥ ~8.7/10 (pylint)
- Modular architecture with clear separation of concerns
- Comprehensive documentation in doc/ folder
- Automated CI/CD via GitHub Actions
- React component-based frontend architecture

