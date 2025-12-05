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
1. **Automated Data Collection**: Systematically collecting data from 28,256 Seattle-based GitHub users
2. **Intelligent Ranking**: Using a multi-factor SSR (Seattle Source Ranker) algorithm that considers popularity, maintenance, and project health
3. **Interactive Visualization**: Providing a web-based interface for exploring projects by language, PyPI status, and other criteria
4. **Daily Updates**: Maintaining fresh data through automated collection and deployment

### Project Goals
- Provide a comprehensive, searchable database of Seattle open-source projects
- Rank projects using quality metrics beyond simple popularity
- Support multiple user personas from recruiters to students
- Maintain data freshness through automated daily updates
- Serve as a tool for both Python package distribution (via pip install) and web-based exploration

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
**Rate Limits**: 5,000 requests/hour per token (30,000/hour with 6 tokens)

**Data Collected**:
- **User Discovery** (GraphQL Search API):
  - Seattle-based users via location filters (76 optimized queries)
  - Handles both User and Organization account types
  - Filters by follower count and repository count for quality
  
- **Repository Metadata** (REST API):
  - Repository name, description, owner
  - Stars, forks, watchers counts
  - Open issues count
  - Primary programming language
  - Topics/tags
  - Creation date, last push date
  - Homepage URL, repository URL

**Data Characteristics**:
- **Granularity**: Individual repository level
- **Freshness**: Updated daily via automated collection
- **Volume**: ~457,212 projects from 28,256 users
- **Completeness**: Full metadata for public repositories

### 3.2 PyPI (Python Package Index)

**Type**: JSON API and package registry  
**Access**: Public API, no authentication required

**Data Collected**:
- Complete list of published package names (707,093 packages)
- Used for offline matching against GitHub projects

**Data Characteristics**:
- **Granularity**: Package name level
- **Freshness**: Updated periodically (cache refreshed as needed)
- **Usage**: Binary classification (on PyPI / not on PyPI)
- **Matching Strategy**: Multiple algorithms including:
  - Direct name matching
  - Prefix removal (python-, py-, django-, flask-, pytest-)
  - Underscore/hyphen normalization
  - Manual mappings for edge cases

### 3.3 Data Integration

**Join Strategy**:
Projects are matched between GitHub and PyPI using:
1. **Primary**: Repository name matching with normalization
2. **Validation**: Topic checking (pypi, python-package, pip)
3. **Filtering**: Generic name exclusion (awesome-, tutorial-, etc.)

**Data Flow**:
```
GitHub API → User Collection → Repository Collection → PyPI Matching → Scoring → Web Interface
```

**Data Quality**:
- **Coverage**: 28,256 Seattle users, 457,212 projects
- **Precision**: 100% for PyPI matching (zero false positives)
- **Detection Rate**: ~1.89% of Python projects are on PyPI (1,025 packages)
- **Update Frequency**: Daily automated collection at midnight Seattle time

---

## 4. Use Cases

### Use Case 1: Technical Recruiter Discovering Local Talent

**Objective**: Jessica, a technical recruiter at Amazon, wants to find senior Python developers in Seattle with strong open-source contributions for an upcoming role.

**User Interactions**:

1. **Access System**
   - Jessica visits https://thomas0829.github.io/Seattle-Source-Ranker/
   - Sees homepage with total statistics (457,212 projects, 2.4M stars)

2. **Navigate to Python Rankings**
   - Clicks "Python Rankings" navigation link
   - Views page showing ~54,188 Python projects from Seattle

3. **Filter and Search**
   - Uses search bar to type "machine learning" 
   - System provides autocomplete suggestions for topics and owners
   - Filters results to projects with PyPI badge (indicating production-ready packages)

4. **Review Project Details**
   - Browses paginated results (50 projects per page)
   - For each project, sees:
     * SSR Score (e.g., 8,432.15)
     * Stars, Forks, Watchers counts
     * Last activity date
     * PyPI badge (10% bonus applied)
     * Topics/tags
     * Direct links to GitHub repository and owner profile

5. **Identify Candidates**
   - Clicks on promising project owners' GitHub profiles
   - Reviews their public contributions
   - Records candidate information for outreach

**Expected Outcome**: Jessica identifies 5-10 high-quality Python developers with active PyPI packages, indicating production-level Python expertise. The SSR score helps her prioritize candidates by combining popularity with code quality and maintenance activity.

---

### Use Case 2: Software Engineer Using Package as Library

**Objective**: Alex, a software engineer, wants to programmatically analyze Seattle projects for a data visualization project at his company.

**User Interactions**:

1. **Install Package**
   ```bash
   pip install seattle-source-ranker
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
   
   projects = [
       {'name': 'requests', 'language': 'Python', 'topics': ['http']},
       {'name': 'flask', 'language': 'Python', 'topics': ['web-framework']},
       {'name': 'my-project', 'language': 'Python', 'topics': []}
   ]
   
   results = checker.batch_check(projects)
   # Returns: [True, True, False]
   ```

4. **Manage GitHub Tokens**
   ```python
   from seattle_source_ranker.tokens import TokenManager
   
   tm = TokenManager()  # Loads from .env.tokens
   token = tm.get_token()  # Gets best available token
   
   limit_info = tm.check_rate_limit()
   print(f"Remaining: {limit_info['remaining']}/5000")
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
User → Homepage → Rankings Page → Filter/Search → Project Details → GitHub Profile
```

### Library Usage Workflow
```
pip install → Import modules → Call functions → Integrate into application
```

### Data Collection Workflow (Automated)
```
GitHub Actions Trigger → Celery Workers → Data Collection → PyPI Matching → 
SSR Scoring → JSON Generation → Website Deployment → README Update
```

### Key System Behaviors
- **Real-time Search**: Debounced input with autocomplete suggestions
- **Pagination**: 50 projects per page for performance
- **Score Calculation**: SSR algorithm runs during data generation (not on-demand)
- **PyPI Detection**: Offline matching using cached package list
- **Token Rotation**: Automatic selection of best available GitHub token
- **Error Handling**: Graceful fallback for rate limits and API errors

---

## 6. Non-Functional Requirements

### Performance
- Website loads in < 2 seconds
- Search autocomplete responds within 200ms
- Complete data collection finishes within 90 minutes
- PyPI checking processes 55k projects in < 30 seconds

### Reliability  
- Daily automated updates with failure recovery
- 99%+ uptime for static website (GitHub Pages)
- Zero false positives for PyPI package detection

### Usability
- Mobile-responsive design
- Clear documentation in README and examples/
- Intuitive search and filter interface
- Accessible to users with basic technical knowledge

### Maintainability
- 91+ passing tests with pytest
- Code quality score ≥ 8.75/10 (pylint)
- Modular architecture for easy updates
- Comprehensive documentation in docs/

---

**Document Version**: 1.0  
**Last Updated**: December 4, 2025  
**Authors**: Seattle Source Ranker Team
