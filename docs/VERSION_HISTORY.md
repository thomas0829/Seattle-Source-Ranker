# Version History

## Beta-v4.0 (2025-12-01) - Watchers Validation & Documentation Overhaul

### Highlights
- **Real watchers data** - Fixed watchers field showing real subscribers instead of duplicate stars
- **Data validation** - GraphQL-based validation removes inaccessible repositories (~2%)
- **Parallel processing** - 8-worker implementation for watchers update (8× speedup)
- **Documentation simplification** - README reduced from 644 to 379 lines, better organization
- **Automated watchers update** - Integrated into GitHub Actions workflow

### Data Quality Improvements
- **Watchers validation script** (`scripts/update_watchers.py`)
  - GraphQL batch queries (100 repos per request)
  - Fetches real subscribers count (not duplicate stars)
  - Removes HTTP 451 (legally blocked), deleted, and private repos
  - 8-worker parallel processing: ~30-40 minutes (vs ~5 hours single-threaded)
  - Automatic removal of 8,200 inaccessible repos from 465,423 → 457,223 projects
- **Real data example**: olmocr 16,109 stars → 83 watchers (0.5%, was incorrectly 16,109)

### Frontend Enhancements
- **Watchers display** added to both Overall and Python rankings pages
- **Icon update**: Changed forks icon from 🍴 to 🔀 (Git fork symbol)
- Display format: ⭐ stars | 👁️ watchers | 🔀 forks | 🐛 issues
- Fallback handling for missing watchers data

### Automation Improvements
- **GitHub Actions integration**: Watchers update step added between PyPI generation and frontend
- **Command**: `python3 scripts/update_watchers.py "$LATEST_PROJECTS" --workers 8`
- **Workflow**: Collection → PyPI → **Watchers** → Frontend → Build → Deploy

### Documentation
- **Simplified README**: Removed redundant sections, excessive emojis, and deployment flow diagram
- **Enhanced docs structure**: Clear navigation with "Back to README" links in all docs
- **File management guide**: Clear explanation of local-only vs Git-tracked files
- **Updated .gitignore**: Exclude generated frontend files (pages/, owner_index/, build/)
- **Manual workflow guide**: Step-by-step process with timing and output information

### Technical Details
- **Token efficiency**: 15.5% usage (4,655/30,000 requests per hour)
- **GraphQL aliases**: repo_0, repo_1... for batch efficiency
- **Performance**: 341,979 updated (73.5%), 115,244 unchanged (24.8%)
- **File handling**: Direct overwrite instead of timestamped copies

## Beta-v3.1 (2025-11-15) - GitHub Actions Automation

### Highlights
- **Automated daily collection** - Runs at midnight Seattle time (08:00 UTC)
- **GraphQL Search API** - 76 pre-optimized filters for efficient user discovery
- **Seattle timezone support** - All timestamps in America/Los_Angeles timezone
- **Simplified documentation** - README reduced from 632 to 224 lines (-65%)
- **Separated detailed docs** - Architecture and version history in dedicated files

### Automation Features
- Daily scheduled collection via GitHub Actions
- Automatic README statistics update
- Frontend rebuild and deployment to GitHub Pages
- Intelligent failure protection with rollback
- Auto-cleanup of old data files
- Multi-token rotation (6 GitHub tokens)

### Technical Improvements
- GraphQL Search API: 5000 requests/hour per token (vs REST: 30 requests/min)
- Rate limit optimization with automatic token switching
- Seattle timezone consistency throughout codebase
- Enhanced documentation structure with links to detailed guides

### Documentation
- Created `docs/ARCHITECTURE.md` - Detailed system architecture
- Created `docs/VERSION_HISTORY.md` - Complete version changelog
- Simplified main README with user stories and team contributions
- Added target audience section for students and recruiters

## Beta-v3.0 (2025-11-06) - Major Collection Upgrade

### Highlights
- **481,323 projects collected** (16× increase from 30K)
- **REST API migration** from GraphQL for better stability
- **Topics/tech stack collection** for each repository
- **Enhanced SSR scoring algorithm** with 6 dimensions

### Data Collection
- Switched from GraphQL to REST API
- Individual repo API calls for topics/tech stack
- ~10% of Seattle projects have topics configured
- 8 workers with 16 concurrent tasks for optimal performance

### Frontend Enhancements
- Multi-select checkbox language filtering (replaces tabs)
- "All" option with smart auto-uncheck behavior
- Real-time search with 500ms debounce
- Page jump input for direct navigation
- Hover details with tech stack display
- 9,632 paginated files (50 projects each)

### Scoring Algorithm
- **Base metrics**: Stars (40%), Forks (20%), Watchers (10%)
- **Quality factors**: Age (10%), Activity (10%), Health (10%)
- Logarithmic scaling for better distribution
- Age maturity curve (peak at 3-5 years)
- Recent activity weighting
- Health metrics based on issue management

### Technical Improvements
- PyPI integration infrastructure (ready for Python packages)
- Lazy loading frontend with glass morphism design
- Multi-token rotation system for rate limit handling
- Language classification across 11 major languages
- Project codebase consolidation and cleanup

## Beta-v2.1 (2025-11-04) - Distributed System

### Features
- Distributed collection with Celery + Redis
- Parallel batch processing with multiple workers
- GitHub GraphQL API integration
- **5-7.5× performance improvement** over single-threaded
- Complete English documentation

### Fixes
- Authentication handling
- Import path corrections
- GraphQL query optimization

## Beta-v2.0 (2024-10-30) - SSR Algorithm & Frontend

### Features
- SSR (Seattle Source Ranker) scoring algorithm
- Multi-factor ranking system
- React frontend for data visualization
- JSON data export functionality

### Algorithm
Initial implementation of weighted scoring:
- Stars, forks, watchers combination
- Basic popularity metrics

## Beta-v1.0 (2024-10-25) - Initial Release

### Features
- Basic GitHub API data collection
- Seattle location-based user search
- Simple ranking by star count
- Command-line interface
- Single-threaded processing

### Scope
- Proof of concept
- Manual execution
- Limited scale (< 1,000 projects)

---

## Back to Main Documentation

← [Return to README](../README.md) - Main project documentation and quick start guide
