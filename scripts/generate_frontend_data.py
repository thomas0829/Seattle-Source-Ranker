#!/usr/bin/env python3
"""
Generate paginated frontend data with on-demand loading.
Creates separate JSON files for each page (50 projects per page).
Uses enhanced SSR scoring algorithm with multiple factors.
"""
import json
import os
import math
from collections import defaultdict
from datetime import datetime, timezone

def normalize(value, max_value):
    """Normalize value to 0-1 range"""
    return value / max_value if max_value > 0 else 0

def log_normalize(value, base=10):
    """Logarithmic normalization for better score distribution"""
    return math.log10(value + 1) / math.log10(base)

def age_factor(created_at):
    """
    Calculate age factor (0-1 range)
    Mature projects (2-8 years) get higher scores
    """
    try:
        created_time = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        years = (datetime.now(timezone.utc) - created_time).days / 365.25
        
        # Peak score at 3-5 years, decrease for too old/new
        if years < 0.5:
            return 0.3  # Too new
        elif years < 2:
            return 0.6 + (years - 0.5) * 0.2  # Growing: 0.6-0.9
        elif years < 5:
            return 0.9 + (years - 2) * 0.033  # Peak: 0.9-1.0
        elif years < 8:
            return 1.0 - (years - 5) * 0.05  # Mature: 1.0-0.85
        else:
            return 0.7 - min((years - 8) * 0.03, 0.4)  # Declining: 0.7-0.3
    except:
        return 0.5

def activity_factor(pushed_at, created_at):
    """
    Calculate recent activity factor (0-1 range)
    Recent updates indicate active maintenance
    """
    try:
        pushed_time = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        created_time = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        
        days_since_push = (datetime.now(timezone.utc) - pushed_time).days
        project_age_days = (datetime.now(timezone.utc) - created_time).days
        
        # Avoid division by zero
        if project_age_days < 1:
            return 1.0
        
        # Recent activity is good
        if days_since_push < 7:
            return 1.0
        elif days_since_push < 30:
            return 0.95
        elif days_since_push < 90:
            return 0.85
        elif days_since_push < 180:
            return 0.7
        elif days_since_push < 365:
            return 0.5
        else:
            # Check if abandoned (no update in years)
            return max(0.2, 0.5 - (days_since_push - 365) / 3650)
    except:
        return 0.5

def health_factor(open_issues, stars):
    """
    Calculate project health (0-1 range)
    Issues relative to popularity
    """
    if stars < 10:
        return 1.0 if open_issues < 5 else 0.8
    
    # Issue ratio relative to stars
    issue_ratio = open_issues / (stars + 1)
    
    if issue_ratio < 0.01:
        return 1.0
    elif issue_ratio < 0.05:
        return 0.9
    elif issue_ratio < 0.1:
        return 0.8
    elif issue_ratio < 0.2:
        return 0.6
    else:
        return 0.4

def calculate_github_score(project, max_stars, max_forks, max_watchers):
    """
    Enhanced SSR Algorithm:
    
    Base Metrics (70%):
      - Stars: 40% (primary popularity indicator)
      - Forks: 20% (engagement and derivative work)
      - Watchers: 10% (ongoing interest)
    
    Quality Factors (30%):
      - Age: 10% (project maturity)
      - Activity: 10% (recent maintenance)
      - Health: 10% (issue management)
    
    Uses logarithmic scaling for better distribution
    """
    stars = project.get('stars', 0)
    forks = project.get('forks', 0)
    watchers = project.get('watchers', 0)
    open_issues = project.get('open_issues', 0)
    created_at = project.get('created_at', '2020-01-01T00:00:00Z')
    pushed_at = project.get('pushed_at', created_at)
    
    # Base metrics with logarithmic scaling
    stars_score = log_normalize(stars, base=100000) * 0.40
    forks_score = log_normalize(forks, base=10000) * 0.20
    watchers_score = log_normalize(watchers, base=10000) * 0.10
    
    # Quality factors
    age_score = age_factor(created_at) * 0.10
    activity_score = activity_factor(pushed_at, created_at) * 0.10
    health_score = health_factor(open_issues, stars) * 0.10
    
    # Total score (0-1 range)
    normalized_score = (stars_score + forks_score + watchers_score + 
                       age_score + activity_score + health_score)
    
    # Scale to 0-10000 for better readability
    final_score = int(normalized_score * 10000)
    
    return final_score

def classify_language(language):
    """Classify language into major categories."""
    if not language:
        return 'Other'
    
    language_lower = language.lower()
    
    major_languages = {
        'javascript': 'JavaScript',
        'typescript': 'JavaScript',
        'python': 'Python',
        'java': 'Java',
        'c++': 'C++',
        'c': 'C++',
        'ruby': 'Ruby',
        'go': 'Go',
        'rust': 'Rust',
        'swift': 'Swift',
        'php': 'PHP',
        'kotlin': 'Kotlin',
    }
    
    return major_languages.get(language_lower, 'Other')

def format_project(project, score):
    """Format project data for frontend."""
    return {
        'name': project['name_with_owner'],
        'owner': project['owner']['login'],
        'html_url': project['url'],
        'stars': project['stars'],
        'forks': project['forks'],
        'issues': project.get('open_issues', 0),
        'language': project.get('language', 'Unknown'),
        'description': project.get('description', ''),
        'topics': project.get('topics', []),
        'score': score
    }
# ============================================================
# PyPI-based scoring for Python projects (NEW)
# ============================================================

def load_pypi_index(filename='data/seattle_pypi_projects.json'):
    """
    Build an index from seattle_pypi_projects.json:

        key:  'owner/repo'
        value: {
            'packages': [pkg1, pkg2, ...],
            'max_confidence': float in [0,1]
        }
    """
    if not os.path.exists(filename):
        print(f"⚠️ PyPI data file not found: {filename}")
        return {}

    with open(filename, 'r') as f:
        data = json.load(f)

    projects = data.get('projects', [])
    index = {}

    for item in projects:
        url = item.get('url') or ''
        repo_full_name = None

        # Typical: https://github.com/owner/repo
        prefix = 'https://github.com/'
        if url.startswith(prefix):
            parts = url[len(prefix):].split('/')
            if len(parts) >= 2:
                repo_full_name = parts[0] + '/' + parts[1]

        # Fallback: full_name
        if not repo_full_name:
            repo_full_name = item.get('full_name')

        # Fallback: owner + name
        if not repo_full_name:
            owner = item.get('owner')
            name = item.get('name')
            if owner and name:
                repo_full_name = f'{owner}/{name}'

        if not repo_full_name:
            continue

        entry = index.setdefault(
            repo_full_name,
            {'packages': set(), 'max_confidence': 0.0},
        )

        pkg_name = item.get('name')
        if pkg_name:
            entry['packages'].add(pkg_name)

        conf = item.get('confidence', 0.0) or 0.0
        if conf > entry['max_confidence']:
            entry['max_confidence'] = conf

    # Convert sets to sorted lists for JSON serialization
    for repo, info in index.items():
        info['packages'] = sorted(list(info['packages']))

    print(f"📦 PyPI index built for {len(index)} GitHub repos")
    return index

def calculate_pypi_score(pypi_info):
    """
    Binary PyPI score in [0, 1].

    - Has at least one PyPI package mapping → 1.0
    - Otherwise → 0.0
    """
    if not pypi_info:
        return 0.0

    num_packages = len(pypi_info.get('packages', []))
    if num_packages <= 0:
        return 0.0

    return 1.0

def calculate_python_project_score(base_score, pypi_info):
    """
    Only for Python main-language projects.

    overall_norm = 0.7 * github_norm + 0.3 * pypi_score
    """
    github_norm = base_score / 10000.0
    pypi_score = calculate_pypi_score(pypi_info)  # 0 or 1

    # No PyPI info → keep original score
    if pypi_score <= 0.0:
        return base_score

    final_norm = 0.7 * github_norm + 0.3 * pypi_score
    return int(final_norm * 10000)

def main():
    import sys
    PAGE_SIZE = 50  # 50 projects per page
    
    # Accept filename from command line or use default
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        # Find the latest projects file
        import glob
        files = glob.glob('data/seattle_projects_*.json')
        if not files:
            print("❌ No project data files found in data/")
            return
        data_file = max(files)  # Get the latest file
    
    print(f"📂 Loading data from {data_file}...")
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    projects = data.get('projects', [])
    print(f"📦 Loaded {len(projects):,} projects")

    # NEW: load PyPI mapping for Python projects
    pypi_index = load_pypi_index('data/seattle_pypi_projects.json')
    
    # Find max values for normalization
    max_stars = max((p.get('stars', 0) for p in projects), default=1)
    max_forks = max((p.get('forks', 0) for p in projects), default=1)
    max_watchers = max((p.get('watchers', 0) for p in projects), default=1)
    
    print(f"📊 Max values: stars={max_stars:,}, forks={max_forks:,}, watchers={max_watchers:,}")
    
    # Calculate scores and classify by language
    by_language = defaultdict(list)
    python_pypi_projects = []   # NEW: Python+PyPI view data
    
    for project in projects:
        score = calculate_github_score(project, max_stars, max_forks, max_watchers)
        language_category = classify_language(project.get('language'))
        formatted = format_project(project, score)
        by_language[language_category].append(formatted)

        # NEW: extra Python+PyPI view
        if language_category == 'Python':
            repo_key = project.get('name_with_owner')
            pypi_info = pypi_index.get(repo_key)
            python_score = calculate_python_project_score(score, pypi_info)

            python_entry = format_project(project, python_score)
            python_entry['base_score'] = score
            python_entry['python_score'] = python_score
            python_entry['has_pypi'] = bool(pypi_info)

            if pypi_info:
                python_entry['pypi_packages'] = pypi_info.get('packages', [])
                python_entry['pypi_max_confidence'] = pypi_info.get(
                    'max_confidence', 0.0
                )

            python_pypi_projects.append(python_entry)
    
    # Sort each language by score
    for language in by_language:
        by_language[language].sort(key=lambda x: x['score'], reverse=True)
    
    # Create output directories
    pages_dir = 'frontend/public/pages'
    os.makedirs(pages_dir, exist_ok=True)
    
    pages_build_dir = 'frontend/build/pages'
    os.makedirs(pages_build_dir, exist_ok=True)
    
    # Generate metadata file (total counts per language)
    from zoneinfo import ZoneInfo
    import re
    SEATTLE_TZ = ZoneInfo("America/Los_Angeles")
    
    # Extract date from filename (e.g., seattle_projects_20251120_220648.json)
    filename_match = re.search(r'(\d{8})_(\d{6})', data_file)
    if filename_match:
        date_str = filename_match.group(1)  # YYYYMMDD
        time_str = filename_match.group(2)  # HHMMSS
        data_datetime = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
        data_datetime = data_datetime.replace(tzinfo=ZoneInfo("UTC")).astimezone(SEATTLE_TZ)
        last_updated = data_datetime.strftime("%Y-%m-%d %H:%M:%S %Z")
    else:
        last_updated = datetime.now(SEATTLE_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
    
    metadata = {
        'languages': {},
        'page_size': PAGE_SIZE,
        'last_updated': last_updated
    }
    
    print(f"\n📊 Generating paginated data:")
    
    for language, lang_projects in sorted(by_language.items(), key=lambda x: len(x[1]), reverse=True):
        total_projects = len(lang_projects)
        total_pages = (total_projects + PAGE_SIZE - 1) // PAGE_SIZE  # Ceiling division
        
        metadata['languages'][language] = {
            'total': total_projects,
            'pages': total_pages
        }
        
        # Create directory for this language
        lang_dir = os.path.join(pages_dir, language.lower().replace('+', 'plus'))
        os.makedirs(lang_dir, exist_ok=True)
        
        lang_build_dir = os.path.join(pages_build_dir, language.lower().replace('+', 'plus'))
        os.makedirs(lang_build_dir, exist_ok=True)
        
        # Generate page files
        for page_num in range(total_pages):
            start_idx = page_num * PAGE_SIZE
            end_idx = min(start_idx + PAGE_SIZE, total_projects)
            page_data = lang_projects[start_idx:end_idx]
            
            page_file = os.path.join(lang_dir, f'page_{page_num + 1}.json')
            with open(page_file, 'w') as f:
                json.dump(page_data, f, separators=(',', ':'))
            
            # Copy to build directory
            build_page_file = os.path.join(lang_build_dir, f'page_{page_num + 1}.json')
            with open(build_page_file, 'w') as f:
                json.dump(page_data, f, separators=(',', ':'))
        
        percentage = (total_projects / sum(len(p) for p in by_language.values()) * 100)
        print(f"  ✅ {language}: {total_projects:,} projects ({percentage:.1f}%) → {total_pages} pages")
    
    # Save metadata
    metadata_file = 'frontend/public/metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # NEW: Python-only PyPI-enhanced view
    print("\n🐍 Generating Python+PyPI enhanced view:")
    python_pypi_projects.sort(key=lambda x: x['score'], reverse=True)

    python_total = len(python_pypi_projects)
    python_pages = (python_total + PAGE_SIZE - 1) // PAGE_SIZE

    python_dir = os.path.join(pages_dir, 'python_pypi')
    os.makedirs(python_dir, exist_ok=True)

    python_build_dir = os.path.join(pages_build_dir, 'python_pypi')
    os.makedirs(python_build_dir, exist_ok=True)

    for page_num in range(python_pages):
        start_idx = page_num * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, python_total)
        page_data = python_pypi_projects[start_idx:end_idx]

        page_file = os.path.join(python_dir, f'page_{page_num + 1}.json')
        with open(page_file, 'w') as f:
            json.dump(page_data, f, separators=(',', ':'))

        build_page_file = os.path.join(python_build_dir, f'page_{page_num + 1}.json')
        with open(build_page_file, 'w') as f:
            json.dump(page_data, f, separators=(',', ':'))

    metadata_python = {
        'language': 'Python',
        'view': 'python_pypi',
        'page_size': PAGE_SIZE,
        'last_updated': last_updated,
        'total': python_total,
        'pages': python_pages,
        'description': 'Python projects ranked by GitHub score (70%) and PyPI presence (30%).',
    }

    metadata_python_file = 'frontend/public/metadata_python_pypi.json'
    with open(metadata_python_file, 'w') as f:
        json.dump(metadata_python, f, indent=2)

    with open('frontend/build/metadata_python_pypi.json', 'w') as f:
        json.dump(metadata_python, f, indent=2)

    print(f"  ✅ Python+PyPI: {python_total:,} projects → {python_pages} pages")
    
    # Copy to build
    with open('frontend/build/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Saved metadata to {metadata_file}")
    print(f"✅ Saved Python+PyPI metadata to {metadata_python_file}")
    print(f"\n🎉 Done! Generated {sum(m['pages'] for m in metadata['languages'].values())} page files"
          f" + {python_pages} Python+PyPI pages")
    print(f"   Each page contains up to {PAGE_SIZE} projects")
    print(f"   Total size: ~{sum(m['total'] for m in metadata['languages'].values()):,} projects")
    print(f"   Python+PyPI projects: {python_total:,}")

if __name__ == "__main__":
    main()