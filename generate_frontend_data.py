#!/usr/bin/env python3
"""
Generate ranked data by language for frontend visualization.
Uses the original SSR scoring algorithm.
"""
import json
import math
from collections import defaultdict
from datetime import datetime, timezone

def normalize(value, max_value):
    """Normalize value to 0-1 range"""
    return value / max_value if max_value > 0 else 0

def age_weight(created_at):
    """Calculate age weight based on project creation time (older = higher score)."""
    try:
        created_time = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        years = (datetime.now(timezone.utc) - created_time).days / 365
        return years / (years + 2) if years > 0 else 0.3
    except Exception:
        return 0.3

def health_score(issues):
    """Calculate health score based on open issues count (fewer = better)."""
    return 1 - (issues / (issues + 10))

def calculate_github_score(project, max_stars, max_forks, max_watchers):
    """
    Calculate GitHub score using original SSR algorithm:
    Score = 0.4 * S_norm + 0.25 * F_norm + 0.15 * W_norm + 0.10 * T_age + 0.10 * H_health
    """
    stars = project.get('stars', 0)
    forks = project.get('forks', 0)
    watchers = project.get('watchers', 0)
    issues = project.get('open_issues', 0)
    created_at = project.get('created_at', '2020-01-01T00:00:00Z')
    
    S = normalize(stars, max_stars)
    F = normalize(forks, max_forks)
    W = normalize(watchers, max_watchers)
    T = age_weight(created_at)
    H = health_score(issues)
    
    score = 0.4 * S + 0.25 * F + 0.15 * W + 0.10 * T + 0.10 * H
    return score

def classify_language(language):
    """Classify language into categories."""
    if not language:
        return 'Other'
    
    language_lower = language.lower()
    
    # Python
    if language_lower == 'python':
        return 'Python'
    
    # JavaScript/TypeScript
    if language_lower in ['javascript', 'typescript', 'jsx', 'tsx']:
        return 'JavaScript'
    
    # Java
    if language_lower == 'java':
        return 'Java'
    
    # C/C++
    if language_lower in ['c', 'c++', 'cpp']:
        return 'C++'
    
    # Go
    if language_lower == 'go':
        return 'Go'
    
    # Ruby
    if language_lower == 'ruby':
        return 'Ruby'
    
    # PHP
    if language_lower == 'php':
        return 'PHP'
    
    # Rust
    if language_lower == 'rust':
        return 'Rust'
    
    # Swift
    if language_lower == 'swift':
        return 'Swift'
    
    # Kotlin
    if language_lower == 'kotlin':
        return 'Kotlin'
    
    return 'Other'

def generate_ranked_by_language():
    """Generate ranked data by language from seattle_projects_10000.json."""
    
    # Load projects
    with open('data/seattle_projects_10000.json', 'r') as f:
        projects = json.load(f)
    
    print(f"📦 Loaded {len(projects)} projects")
    
    # Find max values for normalization
    max_stars = max((p.get('stars', 0) for p in projects), default=1)
    max_forks = max((p.get('forks', 0) for p in projects), default=1)
    max_watchers = max((p.get('watchers', 0) for p in projects), default=1)
    
    print(f"📊 Max values: stars={max_stars}, forks={max_forks}, watchers={max_watchers}")
    
    # Calculate scores and classify by language
    by_language = defaultdict(list)
    
    for project in projects:
        score = calculate_github_score(project, max_stars, max_forks, max_watchers)
        language_category = classify_language(project.get('language'))
        
        by_language[language_category].append({
            'name': project['name_with_owner'],
            'owner': project['owner']['login'],
            'html_url': project['url'],
            'stars': project['stars'],
            'forks': project['forks'],
            'issues': project.get('open_issues', 0),
            'language': project.get('language', 'Unknown'),
            'score': round(score, 2)
        })
    
    # Sort each language category by score (descending)
    for language in by_language:
        by_language[language].sort(key=lambda x: x['score'], reverse=True)
    
    # Create metadata
    metadata = {
        'total_projects': len(projects),
        'by_language': {lang: len(repos) for lang, repos in by_language.items()},
        'languages': list(by_language.keys())
    }
    
    # Prepare output
    output = dict(by_language)
    output['metadata'] = metadata
    
    # Print statistics
    print(f"\n📊 Statistics:")
    for lang in sorted(by_language.keys(), key=lambda x: len(by_language[x]), reverse=True):
        count = len(by_language[lang])
        percentage = (count / len(projects)) * 100
        top_project = by_language[lang][0]['name'] if by_language[lang] else 'N/A'
        top_score = by_language[lang][0]['score'] if by_language[lang] else 0
        print(f"  {lang}: {count} ({percentage:.1f}%) - Top: {top_project} (score: {top_score})")
    
    # Save to frontend directories
    output_files = [
        'frontend/public/ranked_by_language_seattle.json',
        'frontend/build/ranked_by_language_seattle.json'
    ]
    
    for output_file in output_files:
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\n✅ Saved to {output_file}")

if __name__ == '__main__':
    generate_ranked_by_language()
