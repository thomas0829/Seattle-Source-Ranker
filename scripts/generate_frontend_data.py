# -*- coding: utf-8 -*-
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
        if years < 2:
            return 0.6 + (years - 0.5) * 0.2  # Growing: 0.6-0.9
        if years < 5:
            return 0.9 + (years - 2) * 0.033  # Peak: 0.9-1.0
        if years < 8:
            return 1.0 - (years - 5) * 0.05  # Mature: 1.0-0.85
        return 0.7 - min((years - 8) * 0.03, 0.4)  # Declining: 0.7-0.3
    except (ValueError, TypeError):
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
        if days_since_push < 30:
            return 0.95
        if days_since_push < 90:
            return 0.85
        if days_since_push < 180:
            return 0.7
        if days_since_push < 365:
            return 0.5
        # Check if abandoned (no update in years)
        return max(0.2, 0.5 - (days_since_push - 365) / 3650)
    except (ValueError, TypeError):
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
    if issue_ratio < 0.05:
        return 0.9
    if issue_ratio < 0.1:
        return 0.8
    if issue_ratio < 0.2:
        return 0.6
    return 0.4

def calculate_github_score(project, _max_stars=None, _max_forks=None, _max_watchers=None):
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

    Note: max_stars, max_forks, max_watchers parameters are kept for backward
    compatibility with tests but are no longer used in the scoring calculation.
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

    # Scale to 0-1000000 to avoid score collisions
    final_score = normalized_score * 1000000

    return final_score

def classify_language(language):
    """Classify language into major categories for frontend display.

    Returns:
        tuple: (category, original_language, is_true_other)
        - category: Frontend category (top 10 languages or 'Other')
        - original_language: Original language name (for detail display)
        - is_true_other: True if truly unrecognized (null/None), False if it's a known language
    """
    if not language:
        return 'Other', 'Other', True  # True Other - will be penalized

    # Top 10 languages by project count (from actual data analysis)
    top_10_languages = {
        'javascript': 'JavaScript',
        'python': 'Python',
        'html': 'HTML',
        'java': 'Java',
        'jupyter notebook': 'Jupyter Notebook',
        'typescript': 'TypeScript',
        'c#': 'C#',
        'ruby': 'Ruby',
        'css': 'CSS',
        'c++': 'C++',
    }

    language_lower = language.lower()

    # Check if it's in top 10
    if language_lower in top_10_languages:
        cat = top_10_languages[language_lower]
        return cat, language, False

    # All other known languages go to "Other" category but keep original name
    # These are real languages, just not in top 10, so no penalty
    return 'Other', language, False

def format_project(project, score, display_language=None):
    """Format project data for frontend.

    Args:
        project: Raw project data
        score: Calculated score (already penalized if needed)
        display_language: Language to display (defaults to original if not specified)
    """
    return {
        'name': project['name_with_owner'],
        'owner': project['owner']['login'],
        'html_url': project['url'],
        'stars': project['stars'],
        'forks': project['forks'],
        'watchers': project.get('watchers', 0),
        'issues': project.get('open_issues', 0),
        'language': display_language or project.get('language', 'Unknown'),
        'description': project.get('description', ''),
        'topics': project.get('topics', []),
        'score': score
    }

def main():
    import sys
    PAGE_SIZE = 50  # 50 projects per page

    # Accept filename from command line or use default
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        # Use standard filename
        data_file = 'data/seattle_projects.json'
        if not os.path.exists(data_file):
            print("[ERROR] No project data file found: data/seattle_projects.json")
            return

    print(f"[DIR] Loading data from {data_file}...")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    projects = data.get('projects', [])
    print(f"[PKG] Loaded {len(projects):,} projects")

    # Find max values for normalization
    max_stars = max((p.get('stars', 0) for p in projects), default=1)
    max_forks = max((p.get('forks', 0) for p in projects), default=1)
    max_watchers = max((p.get('watchers', 0) for p in projects), default=1)

    print(f"[STATS] Max values: stars={max_stars:,}, forks={max_forks:,}, watchers={max_watchers:,}")

    # Calculate scores and classify by language
    by_language = defaultdict(list)
    all_projects = []

    for project in projects:
        base_score = calculate_github_score(project)
        category, original_lang, is_true_other = classify_language(project.get('language'))

        # Apply penalty for truly unrecognized languages
        final_score = base_score * 0.8 if is_true_other else base_score

        formatted = format_project(project, final_score, original_lang)
        by_language[category].append(formatted)
        all_projects.append(formatted)

    # Round all scores to integers before sorting (since base is now 0-1000000)
    for proj in all_projects:
        proj['score'] = int(round(proj['score']))

    # Sort ALL projects globally by score and assign global rank
    all_projects.sort(key=lambda x: x['score'], reverse=True)
    for rank, project in enumerate(all_projects, start=1):
        project['global_rank'] = rank

    # Sort each language by score (they already have global_rank assigned)
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

    # Try to get collected_at from data first (most accurate)
    collected_at = data.get('collected_at')
    if collected_at:
        try:
            # Parse ISO format timestamp
            data_datetime = datetime.fromisoformat(collected_at.replace('Z', '+00:00'))
            # Convert to Seattle timezone
            data_datetime = data_datetime.astimezone(SEATTLE_TZ)
            tz_name = data_datetime.strftime("%Z")  # Will be "PST" or "PDT"
            last_updated = data_datetime.strftime(f"%Y-%m-%d %H:%M:%S {tz_name}")
        except (ValueError, AttributeError):
            collected_at = None
    
    # Fallback: Extract date from filename (e.g., seattle_projects_20251120_220648.json)
    if not collected_at:
        filename_match = re.search(r'(\d{8})_(\d{6})', data_file)
        if filename_match:
            date_str = filename_match.group(1)  # YYYYMMDD
            time_str = filename_match.group(2)  # HHMMSS
            data_datetime = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
            # Filename timestamp is already in PST/PDT (local Seattle time)
            data_datetime = data_datetime.replace(tzinfo=SEATTLE_TZ)
            # Automatically use PST or PDT based on daylight saving time
            tz_name = data_datetime.strftime("%Z")  # Will be "PST" or "PDT"
            last_updated = data_datetime.strftime(f"%Y-%m-%d %H:%M:%S {tz_name}")
        else:
            now = datetime.now(SEATTLE_TZ)
            tz_name = now.strftime("%Z")  # Will be "PST" or "PDT"
            last_updated = now.strftime(f"%Y-%m-%d %H:%M:%S {tz_name}")

    metadata = {
        'languages': {},
        'page_size': PAGE_SIZE,
        'last_updated': last_updated
    }

    print("\n[STATS] Generating paginated data:")

    for language, lang_projects in sorted(by_language.items(), key=lambda x: len(x[1]), reverse=True):
        total_projects = len(lang_projects)
        total_pages = (total_projects + PAGE_SIZE - 1) // PAGE_SIZE  # Ceiling division

        metadata['languages'][language] = {
            'total': total_projects,
            'pages': total_pages
        }

        # Create directory for this language
        # Convert to safe path: C++ -> cplusplus, C# -> csharp
        safe_lang_name = language.lower().replace('+', 'plus').replace('#', 'sharp')
        lang_dir = os.path.join(pages_dir, safe_lang_name)
        os.makedirs(lang_dir, exist_ok=True)

        lang_build_dir = os.path.join(pages_build_dir, safe_lang_name)
        os.makedirs(lang_build_dir, exist_ok=True)

        # Generate page files
        for page_num in range(total_pages):
            start_idx = page_num * PAGE_SIZE
            end_idx = min(start_idx + PAGE_SIZE, total_projects)
            page_data = lang_projects[start_idx:end_idx]

            page_file = os.path.join(lang_dir, f'page_{page_num + 1}.json')
            with open(page_file, 'w', encoding='utf-8') as f:
                json.dump(page_data, f, separators=(',', ':'))

            # Copy to build directory
            build_page_file = os.path.join(lang_build_dir, f'page_{page_num + 1}.json')
            with open(build_page_file, 'w', encoding='utf-8') as f:
                json.dump(page_data, f, separators=(',', ':'))

        percentage = (total_projects / sum(len(p) for p in by_language.values()) * 100)
        print(f"  [OK] {language}: {total_projects:,} projects ({percentage:.1f}%) → {total_pages} pages")

    # Generate mixed "All" pages (top 10000 by global_rank)
    print("\n[INFO] Generating mixed 'All' pages (top 10000)...")
    all_projects_sorted = sorted(all_projects, key=lambda x: x['global_rank'])[:10000]
    
    all_dir = os.path.join(pages_dir, 'all')
    os.makedirs(all_dir, exist_ok=True)
    
    all_build_dir = os.path.join(pages_build_dir, 'all')
    os.makedirs(all_build_dir, exist_ok=True)
    
    total_all_pages = (len(all_projects_sorted) + PAGE_SIZE - 1) // PAGE_SIZE  # Should be 200
    
    for page_num in range(total_all_pages):
        start_idx = page_num * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, len(all_projects_sorted))
        page_data = all_projects_sorted[start_idx:end_idx]
        
        page_file = os.path.join(all_dir, f'page_{page_num + 1}.json')
        with open(page_file, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, separators=(',', ':'))
        
        # Copy to build directory
        build_page_file = os.path.join(all_build_dir, f'page_{page_num + 1}.json')
        with open(build_page_file, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, separators=(',', ':'))
    
    print(f"  [OK] All (mixed): 10,000 projects → {total_all_pages} pages")
    
    # Calculate min and max scores from ALL projects (not just top 10000)
    # This ensures the score bars scale correctly across the full range
    all_scores = [p['score'] for p in all_projects]
    all_max_score = max(all_scores) if all_scores else 0
    all_min_score = min(all_scores) if all_scores else 0
    
    # Add to metadata
    metadata['languages']['All'] = {
        'total': len(all_projects),  # Total number of all projects, not just top 10k displayed
        'pages': total_all_pages,
        'max_score': all_max_score,
        'min_score': all_min_score
    }

    # Special handling for Python: Generate separate rankings WITH PyPI bonus
    # This creates pages/python_pypi/ for the dedicated Python Rankings page
    # while pages/python/ (already generated above) is used by Overall Rankings
    print("\n[INFO] Generating Python rankings with PyPI bonus (for Python Rankings page)...")
    
    # Load PyPI data
    pypi_file = 'data/seattle_pypi_projects.json'
    pypi_projects = set()
    if os.path.exists(pypi_file):
        with open(pypi_file, 'r', encoding='utf-8') as f:
            pypi_data = json.load(f)
            projects_list = pypi_data.get('projects', [])
            for proj in projects_list:
                # Build full_name key: owner/name
                owner = proj.get('owner', '')
                name = proj.get('name', '')
                if owner and name:
                    full_name = f"{owner}/{name}".lower()
                    pypi_projects.add(full_name)
        print(f"  [OK] Loaded {len(pypi_projects):,} PyPI projects")
    
    # Load Top PyPI data
    top_pypi_file = 'data/seattle_top_pypi_matches.json'
    top_pypi_projects = set()
    if os.path.exists(top_pypi_file):
        with open(top_pypi_file, 'r', encoding='utf-8') as f:
            top_pypi_data = json.load(f)
            # Try different possible keys: matched_projects, projects, or matches
            matches_list = top_pypi_data.get('matched_projects', 
                          top_pypi_data.get('projects', 
                          top_pypi_data.get('matches', [])))
            for proj in matches_list:
                owner = proj.get('owner', '')
                # Try both 'name' and 'repo' keys
                name = proj.get('name', proj.get('repo', ''))
                if owner and name:
                    full_name = f"{owner}/{name}".lower()
                    top_pypi_projects.add(full_name)
        print(f"  [OK] Loaded {len(top_pypi_projects):,} Top PyPI projects")
    
    # Get Python projects and recalculate scores with tiered PyPI bonus
    # Note: Make a DEEP COPY to avoid modifying the original by_language['Python']
    # which is used by Overall Rankings (pages/python/)
    if 'Python' in by_language:
        import copy
        python_pypi_projects = copy.deepcopy(by_language['Python'])
        PYPI_TIER1_MULTIPLIER = 1.05  # Any PyPI package
        PYPI_TIER2_MULTIPLIER = 1.10  # Top 15k PyPI package
        
        # Add tiered PyPI bonus to scores
        for proj in python_pypi_projects:
            project_key = proj['name'].lower()
            on_top_pypi = project_key in top_pypi_projects
            # If it's top PyPI, it must be on PyPI
            on_pypi = project_key in pypi_projects or on_top_pypi
            base_score = proj['score']
            
            # Apply tiered multipliers
            final_score = base_score
            if on_pypi:
                final_score *= PYPI_TIER1_MULTIPLIER
            if on_top_pypi:
                final_score *= PYPI_TIER2_MULTIPLIER
            
            proj['score'] = int(round(final_score))
            proj['on_pypi'] = on_pypi
            proj['top_pypi'] = on_top_pypi
        
        # Re-sort by score (no separate final_score)
        python_pypi_projects.sort(key=lambda x: x['score'], reverse=True)
        
        # Add python_rank to each project for consistent ranking
        for rank, proj in enumerate(python_pypi_projects, start=1):
            proj['python_rank'] = rank
        
        # Generate Python+PyPI pages in separate directory
        total_python_pypi = len(python_pypi_projects)
        total_python_pypi_pages = (total_python_pypi + PAGE_SIZE - 1) // PAGE_SIZE
        
        python_pypi_dir = os.path.join(pages_dir, 'python_pypi')
        os.makedirs(python_pypi_dir, exist_ok=True)
        python_pypi_build_dir = os.path.join(pages_build_dir, 'python_pypi')
        os.makedirs(python_pypi_build_dir, exist_ok=True)
        
        for page_num in range(total_python_pypi_pages):
            start_idx = page_num * PAGE_SIZE
            end_idx = min(start_idx + PAGE_SIZE, total_python_pypi)
            page_data = python_pypi_projects[start_idx:end_idx]
            
            # Keep score (with PyPI bonus) and on_pypi for frontend display
            clean_data = []
            for proj in page_data:
                # Keep all fields including score with PyPI bonus, on_pypi, and top_pypi
                clean_data.append(proj)
            
            page_file = os.path.join(python_pypi_dir, f'page_{page_num + 1}.json')
            with open(page_file, 'w', encoding='utf-8') as f:
                json.dump(clean_data, f, separators=(',', ':'))
            
            build_page_file = os.path.join(python_pypi_build_dir, f'page_{page_num + 1}.json')
            with open(build_page_file, 'w', encoding='utf-8') as f:
                json.dump(clean_data, f, separators=(',', ':'))
        
        print(f"  [OK] Python+PyPI: {total_python_pypi:,} projects → {total_python_pypi_pages} pages (with PyPI bonus, for Python Rankings page)")
        
        # Calculate min and max scores for Python+PyPI
        python_scores = [p['score'] for p in python_pypi_projects]
        python_max_score = max(python_scores) if python_scores else 0
        python_min_score = min(python_scores) if python_scores else 0
        
        # Add Python+PyPI metadata
        metadata['languages']['Python_PyPI'] = {
            'total': total_python_pypi,
            'pages': total_python_pypi_pages,
            'max_score': python_max_score,
            'min_score': python_min_score
        }
        
        # Generate Python owner index (for faster owner search)
        print("\n[INFO] Generating Python owner index (with PyPI bonus)...")
        python_owner_index = defaultdict(list)
        
        for proj in python_pypi_projects:
            # Use score already calculated above (includes PyPI bonus)
            python_owner_index[proj['owner']].append({
                'name': proj['name'],
                'owner': proj['owner'],
                'html_url': proj['html_url'],
                'stars': proj['stars'],
                'forks': proj['forks'],
                'watchers': proj.get('watchers', 0),
                'issues': proj['issues'],
                'language': 'Python',
                'description': proj.get('description', ''),
                'topics': proj.get('topics', []),
                'score': proj['score'],  # Already includes PyPI bonus
                'on_pypi': proj['on_pypi'],  # Already set above
                'top_pypi': proj.get('top_pypi', False),
                'python_rank': proj['python_rank']
            })
        
        # Sort each owner's projects by score
        for owner in python_owner_index:
            python_owner_index[owner].sort(key=lambda x: x['score'], reverse=True)
        
        # Split index by first character
        python_owner_groups = defaultdict(dict)
        for owner, projects in python_owner_index.items():
            first_char = owner[0].lower() if owner else 'other'
            if not first_char.isalnum():
                first_char = 'other'
            python_owner_groups[first_char][owner] = projects
        
        # Create python_owner_index directory
        python_owner_dir = 'frontend/public/python_owner_index'
        os.makedirs(python_owner_dir, exist_ok=True)
        
        python_owner_build_dir = 'frontend/build/python_owner_index'
        os.makedirs(python_owner_build_dir, exist_ok=True)
        
        # Save each group
        total_python_owners = 0
        for char, owners in python_owner_groups.items():
            index_file = os.path.join(python_owner_dir, f'{char}.json')
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(owners, f, separators=(',', ':'))
            
            # Copy to build
            build_file = os.path.join(python_owner_build_dir, f'{char}.json')
            with open(build_file, 'w', encoding='utf-8') as f:
                json.dump(owners, f, separators=(',', ':'))
            
            total_python_owners += len(owners)
        
        print(f"  [OK] Python owner index: {total_python_owners:,} unique owners")
    
    # Save metadata
    metadata_file = 'frontend/public/metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    # Copy to build
    with open('frontend/build/metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n[OK] Saved metadata to {metadata_file}")

    # Generate owner index for fast user searches (split into chunks)
    print("\n[INFO] Generating owner index...")
    owner_index = defaultdict(list)

    for language, lang_projects in by_language.items():
        for project in lang_projects:
            owner_index[project['owner']].append({
                'name': project['name'],
                'owner': project['owner'],
                'html_url': project['html_url'],
                'stars': project['stars'],
                'forks': project['forks'],
                'watchers': project.get('watchers', 0),
                'issues': project['issues'],
                'language': language,
                'description': project.get('description', ''),
                'topics': project.get('topics', []),
                'score': project['score'],
                'global_rank': project['global_rank']
            })

    # Sort each owner's projects by score
    for owner in owner_index:
        owner_index[owner].sort(key=lambda x: x['score'], reverse=True)

    # Split index into multiple files to avoid GitHub size limits
    # Group owners by first character for faster loading
    owner_groups = defaultdict(dict)
    for owner, projects in owner_index.items():
        first_char = owner[0].lower() if owner else 'other'
        if not first_char.isalnum():
            first_char = 'other'
        owner_groups[first_char][owner] = projects

    # Create owner_index directory
    owner_index_dir = 'frontend/public/owner_index'
    os.makedirs(owner_index_dir, exist_ok=True)

    owner_build_dir = 'frontend/build/owner_index'
    os.makedirs(owner_build_dir, exist_ok=True)

    # Save each group
    total_owners = 0
    for char, owners in owner_groups.items():
        index_file = os.path.join(owner_index_dir, f'{char}.json')
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(owners, f, separators=(',', ':'))

        # Copy to build
        build_file = os.path.join(owner_build_dir, f'{char}.json')
        with open(build_file, 'w', encoding='utf-8') as f:
            json.dump(owners, f, separators=(',', ':'))

        total_owners += len(owners)
        print(f"  [OK] {char}.json: {len(owners):,} owners")

    print(f"[OK] Generated split owner index with {total_owners:,} unique owners")

    print(f"\n[DONE] Done! Generated {sum(m['pages'] for m in metadata['languages'].values())} page files")
    print(f"   Each page contains up to {PAGE_SIZE} projects")
    print(f"   Total size: ~{sum(m['total'] for m in metadata['languages'].values()):,} projects")

if __name__ == "__main__":
    main()
