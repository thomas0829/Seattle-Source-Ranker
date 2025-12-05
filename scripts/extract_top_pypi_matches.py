#!/usr/bin/env python3
"""
Extract Seattle projects that appear in top PyPI packages ranking.

This script matches Seattle PyPI projects against the top 15,000 PyPI packages
by download count, producing a dataset that can be used to adjust scoring algorithms.

Output includes:
- Match statistics
- Detailed list with download counts
- JSON file for programmatic use
"""

import json
from pathlib import Path
from datetime import datetime


def load_seattle_projects(data_dir: Path) -> list:
    """Load Seattle PyPI projects from JSON file."""
    seattle_file = data_dir / "seattle_pypi_projects.json"
    with open(seattle_file, 'r') as f:
        data = json.load(f)
    return data['projects']


def load_top_pypi_packages(data_dir: Path) -> dict:
    """Load top PyPI packages ranking."""
    ranking_file = data_dir / "top_pypi_packages.json"
    with open(ranking_file, 'r') as f:
        data = json.load(f)
    
    # Create lookup dict: package_name -> {rank, downloads}
    lookup = {}
    for i, row in enumerate(data['rows'], 1):
        pkg_name = row['project'].lower()
        lookup[pkg_name] = {
            'rank': i,
            'downloads': row['download_count'],
            'package_name': row['project']  # Original case
        }
    
    return {
        'lookup': lookup,
        'last_update': data.get('last_update', 'unknown'),
        'total_packages': len(data['rows'])
    }


def match_projects(seattle_projects: list, top_pypi_data: dict) -> dict:
    """Match Seattle projects against top PyPI ranking."""
    lookup = top_pypi_data['lookup']
    
    matched = []
    unmatched = []
    
    for project in seattle_projects:
        pkg_name = project.get('name', '').lower()
        
        if pkg_name in lookup:
            pypi_info = lookup[pkg_name]
            matched.append({
                'owner': project.get('owner'),
                'repo': project.get('name'),
                'stars': project.get('stars', 0),
                'description': project.get('description', ''),
                'url': project.get('url', ''),
                'pypi_rank': pypi_info['rank'],
                'pypi_downloads': pypi_info['downloads'],
                'pypi_package': pypi_info['package_name']
            })
        else:
            unmatched.append(project)
    
    # Sort by download count (descending)
    matched.sort(key=lambda x: x['pypi_downloads'], reverse=True)
    
    return {
        'matched': matched,
        'unmatched': unmatched,
        'stats': {
            'total_seattle_projects': len(seattle_projects),
            'matched_count': len(matched),
            'unmatched_count': len(unmatched),
            'match_rate': f"{len(matched) / len(seattle_projects) * 100:.2f}%"
        }
    }


def categorize_by_downloads(matched_projects: list) -> dict:
    """Categorize matched projects by download volume."""
    categories = {
        'mega': [],      # > 100M downloads
        'major': [],     # 10M - 100M
        'popular': [],   # 1M - 10M
        'notable': [],   # 100K - 1M
        'moderate': [],  # 10K - 100K
        'emerging': []   # < 10K
    }
    
    for proj in matched_projects:
        downloads = proj['pypi_downloads']
        if downloads >= 100_000_000:
            categories['mega'].append(proj)
        elif downloads >= 10_000_000:
            categories['major'].append(proj)
        elif downloads >= 1_000_000:
            categories['popular'].append(proj)
        elif downloads >= 100_000:
            categories['notable'].append(proj)
        elif downloads >= 10_000:
            categories['moderate'].append(proj)
        else:
            categories['emerging'].append(proj)
    
    return categories


def print_report(results: dict, categories: dict, top_pypi_data: dict):
    """Print human-readable report."""
    stats = results['stats']
    matched = results['matched']
    
    print("=" * 80)
    print("Seattle Projects in Top PyPI Packages Ranking")
    print("=" * 80)
    print(f"\nData Source: top-pypi-packages (last update: {top_pypi_data['last_update']})")
    print(f"Total top packages: {top_pypi_data['total_packages']:,}")
    print()
    print(f"Total Seattle PyPI projects: {stats['total_seattle_projects']:,}")
    print(f"Matched (in top 15K):        {stats['matched_count']:,}")
    print(f"Unmatched:                   {stats['unmatched_count']:,}")
    print(f"Match rate:                  {stats['match_rate']}")
    print()
    
    print("Download Volume Categories:")
    print("-" * 80)
    for category_name, count_label in [
        ('mega', 'Mega (>100M)'),
        ('major', 'Major (10M-100M)'),
        ('popular', 'Popular (1M-10M)'),
        ('notable', 'Notable (100K-1M)'),
        ('moderate', 'Moderate (10K-100K)'),
        ('emerging', 'Emerging (<10K)')
    ]:
        count = len(categories[category_name])
        print(f"  {count_label:20} {count:4} projects")
    print()
    
    print("Top 20 Most Downloaded Seattle Projects:")
    print("-" * 80)
    for i, proj in enumerate(matched[:20], 1):
        owner = proj['owner']
        repo = proj['repo']
        stars = proj['stars']
        downloads = proj['pypi_downloads']
        rank = proj['pypi_rank']
        print(f"{i:3}. {owner}/{repo:30} ⭐ {stars:6,}  📥 {downloads:>15,}  (Rank #{rank:,})")
    print()
    
    # Show some interesting stats
    if categories['mega']:
        print("🏆 Mega Projects (>100M downloads/month):")
        print("-" * 80)
        for proj in categories['mega']:
            print(f"  • {proj['owner']}/{proj['repo']}")
            print(f"    Downloads: {proj['pypi_downloads']:,}")
            print(f"    Stars: {proj['stars']:,}")
            print(f"    Rank: #{proj['pypi_rank']:,}")
            print()


def save_results(results: dict, categories: dict, output_dir: Path):
    """Save results to standard JSON file."""
    # Use standard filename without timestamp
    output_file = output_dir / "seattle_top_pypi_matches.json"
    with open(output_file, 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'statistics': results['stats'],
            'matched_projects': results['matched'],
            'categories': {
                name: len(projects) 
                for name, projects in categories.items()
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved to: {output_file}")


def main():
    """Main execution."""
    # Setup paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    
    print("Loading Seattle projects...")
    seattle_projects = load_seattle_projects(data_dir)
    
    print("Loading top PyPI packages ranking...")
    top_pypi_data = load_top_pypi_packages(data_dir)
    
    print("Matching projects...")
    results = match_projects(seattle_projects, top_pypi_data)
    
    print("Categorizing by download volume...")
    categories = categorize_by_downloads(results['matched'])
    
    # Print report
    print_report(results, categories, top_pypi_data)
    
    # Save results
    save_results(results, categories, data_dir)
    
    print("\n" + "=" * 80)
    print("✓ Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
