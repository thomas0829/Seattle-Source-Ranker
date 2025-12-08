# Version History

## Beta-v4.2 (2025-12-07) - Tiered PyPI Scoring System

### Highlights
- **Tiered PyPI bonuses** - Two-tier system: ×1.05 (any PyPI) + ×1.10 (Top 15k global)
- **Score scale expansion** - Changed from 0-10,000 to 0-1,000,000 points to avoid collisions
- **Top 15k PyPI integration** - 28 Seattle packages in global Top 15,000 most-downloaded
- **Luxury badge design** - Gold-to-purple gradient badge for Top 15k packages
- **Backend-only calculation** - Frontend displays scores directly, no frontend multipliers

### Tiered Scoring System
- **Tier 1 - Any PyPI Package**: ×1.05 multiplier
  - Applies to ~1,071 packages (2.74% of Python projects)
  - Rewards publication, ecosystem integration, pip-installability
  
- **Tier 2 - Top 15k Global PyPI**: ×1.10 additional multiplier
  - Applies to ~28 packages (0.07% of Python projects)
  - Honors global impact, millions of downloads
  - Combined with Tier 1: ×1.155 total bonus (+15.5%)

- **Rationale**: Simple tiered system easier to understand than complex gap-based bonuses
- **Architecture**: Backend calculates all scoring, frontend only displays

### Score Scale Enhancement
- **Previous**: 0-10,000 range with frontend ×100 display multiplier
- **Current**: 0-1,000,000 range calculated in backend
- **Benefits**: 
  - Avoids score collisions
  - Cleaner architecture (no frontend calculation)
  - Direct display without conversion
- **Example**: Project with 756k base score → 793,800 (PyPI) or 873,180 (Top 15k)

### Top 15k PyPI Integration
- **Data source**: seattle_top_pypi_matches.json
- **Coverage**: 28 Seattle packages in global Top 15,000
- **Detection rate**: 0.07% of Python projects (2.6% of PyPI packages)
- **Examples**: facenet-pytorch, azure-cli-core, azure-mgmt packages
- **Flexible loading**: Supports 'matched_projects', 'projects', 'matches' keys and 'name'/'repo' fields

### Frontend Enhancements
- **Top 15k PyPI badge**:
  - Luxury gold-to-purple gradient (7 colors)
  - Glow effects: rgba(255, 215, 0, 0.4) and rgba(139, 92, 246, 0.2)
  - 4-second animation with 300% background size
  - Text: "TOP 15K PYPI" in bold uppercase
  
- **Badge priority**: Top 15k badge shown exclusively (hides regular PyPI badge)
- **Regular PyPI badge**: Rainbow gradient retained for standard packages
- **Display simplification**: Removed frontend score calculations

### Backend Implementation
- **generate_frontend_data.py**:
  - Load Top PyPI data with fallback key matching
  - Apply tiered multipliers: `final_score *= 1.05` then `*= 1.10`
  - Ensure Top PyPI implies on_pypi flag
  - Round scores to integers
  - Use single 'score' field (removed separate 'final_score')

- **Constants**:
  - `PYPI_TIER1_MULTIPLIER = 1.05`
  - `PYPI_TIER2_MULTIPLIER = 1.10`
  - Combined effect: 1.05 × 1.10 = 1.155 (+15.5%)

### Documentation Updates
- **Component Specification**: Updated PyPI stats, tiered scoring formula, 0-1M scale
- **ScoringPage.js**: Replaced 10% flat bonus with tiered system explanation
- **HomePage.js**: Updated PyPI section with tiered bonus details
- **All docs**: Corrected statistics (1,071 PyPI, 28 Top 15k, 2.74%, 0.07%)

### Statistics Updates
- **PyPI packages**: 1,025 → 1,071 (detection rate: 1.89% → 2.74%)
- **Top 15k packages**: New - 28 packages (0.07% of Python projects)
- **Paginated files**: 9,632 → 7,265 (optimized pagination)
- **Score distribution**: More natural with 0-1M scale

## Beta-v4.1 (2025-12-05) - Python Page Optimization & Ranking Fix

### Highlights
- **Fixed ranking system** - Python projects now preserve global ranks during filtering/search
- **Performance boost** - Owner search ~100× faster (<0.1s vs 10+ seconds)
- **Enhanced search** - 12 suggestions (8 owners + 4 topics) with lazy loading
- **UI consistency** - All animations aligned with Overall page
- **Improved UX** - Better scroll behavior and loading indicators

### Ranking System Fix
- **Global rank preservation** - Added `python_rank` field (1-39,067) to all Python projects
- **Consistent ordering** - Rankings remain stable during owner filtering or search
- **Example**: chriskiehl/Gooey always shows #7 (global rank), not #1 when filtering by owner
- **Data structure**: Both page files and owner index include `python_rank`

### Performance Optimizations
- **python_owner_index** - 10,254 unique Python owners split by first character (a-z, 0-9, other)
- **Owner search speed**: ~100× faster (loads 1 index file vs 782 pages)
- **Search suggestions**: On-demand loading by first character, can suggest from all 10K+ owners
- **Page caching**: <0.5s load time with intelligent cache management

### UI/UX Improvements
- **Animation consistency**:
  - Added `tableFlash` state for scan animations
  - Added `skipScanAnimationRef` to control animation types
  - Row animations (`updatingRows`) triggered correctly on all interactions
- **Loading behavior**: Spinner shows below search bar (matches Overall page)
- **Scroll behavior**: Returns to top when navigating to page 1
- **Hover effects**: Removed distracting translateY and pulse animations
- **Search suggestions**: Increased limit from 8 to 12 (more space without language filters)

### Frontend Enhancements
- **Search suggestion improvements**:
  - Owner suggestions: Load from python_owner_index (not limited to current page)
  - Topic suggestions: 35+ Python-specific topics (ML, data science, web frameworks, etc.)
  - Smart limits: Max 8 owners, 4 topics for balanced display
- **Animation timing**: Matches Overall page (50ms delay for updatingRows, 2s tableFlash)
- **Pagination fix**: Buttons no longer disappear after clearing owner search

### Build & Deployment
- **Optimized build script**: `rm -rf build/data` before copying to exclude large files
- **Symlink handling**: Dev uses symlink, CI/CD copies actual files
- **Size reduction**: Only seattle_pypi_projects.json (378KB) deployed, not full dataset (178MB)
- **Deployment success**: Fixed GitHub Pages 100MB file size limit issue

### Technical Details
- **GITHUB_WEIGHT**: Unified to 1.0 across frontend and backend
- **PYPI_BONUS**: 0.1 (multiplicative: final_score = base_score × 1.1)
- **Data generation**: python_rank added during sorting, preserved through pipeline
- **Caching strategy**: pageCache for loaded pages, lazy loading for owner index

## Beta-v4.0 (2025-12-01) - Watchers Validation & Documentation Overhaul

### Highlights
- **Real watchers data** - Fixed watchers field showing real subscribers instead of duplicate stars
- **Data validation** - GraphQL-based validation removes inaccessible repositories (~2%)
- **Parallel processing** - 8-worker implementation for watchers update (8× speedup)
- **Documentation simplification** - README reduced from 644 to 379 lines, better organization
- **Automated watchers update** - Integrated into GitHub Actions workflow

### Data Quality Improvements
- **Secondary data update script** (`scripts/secondary_update.py`)
  - GraphQL batch queries (100 repos per request)
  - Fetches real subscribers count (not duplicate stars)
  - Removes HTTP 451 (legally blocked), deleted, and private repos
  - 8-worker parallel processing: ~30-40 minutes (vs ~5 hours single-threaded)
  - Automatic removal of 8,200 inaccessible repos from 465,423 → 457,223 projects
- **Real data example**: olmocr 16,109 stars → 83 watchers (0.5%, was incorrectly 16,109)

### Frontend Enhancements
- **Watchers display** added to both Overall and Python rankings pages
- **Icon update**: Changed forks icon from fork-and-knife to git-fork symbol
- Display format: [STAR] stars | [WATCH] watchers | [FORK] forks | [BUG] issues
- Fallback handling for missing watchers data

### Automation Improvements
- **GitHub Actions integration**: Watchers update step added between PyPI generation and frontend
- **Command**: `python3 scripts/secondary_update.py "$LATEST_PROJECTS"`
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
- Functional and Component Specifications - Complete system design
- Simplified documentation structure with focused guides
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
