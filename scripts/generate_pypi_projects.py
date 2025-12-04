#!/usr/bin/env python3
"""
Generate list of Python projects that are on PyPI.
Outputs a JSON file with GitHub project names that have PyPI packages.
"""
import json
import sys
import glob
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.pypi_checker import PyPIChecker


def main():
    """Main function to check Python projects and generate PyPI list"""

    # Find the latest projects file
    project_files = glob.glob('data/seattle_projects_*.json')
    if not project_files:
        print("❌ No project data files found in data/")
        return

    data_file = max(project_files)
    print("📂 Loading data from {data_file}...")

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Get projects data
    if isinstance(data, dict) and 'projects' in data:
        all_projects = data['projects']
    elif isinstance(data, list):
        all_projects = data
    else:
        print("❌ Unexpected data format")
        return

    # Filter Python projects
    python_projects = [p for p in all_projects if p.get('language') == 'Python']
    print("🐍 Found {len(python_projects):,} Python projects")

    # Initialize PyPI checker
    print("\n📦 Initializing PyPI checker...")
    checker = PyPIChecker()
    print()

    # Check all Python projects
    print("🔍 Checking which projects are on PyPI...")
    print("   This may take a few seconds...")

    pypi_projects = []
    stats = {
        'total_checked': 0,
        'on_pypi': 0,
        'not_on_pypi': 0,
        'by_confidence': {
            'very_high': 0,  # > 0.9
            'high': 0,       # 0.8-0.9
            'medium': 0,     # 0.7-0.8
            'low': 0         # 0.4-0.7
        },
        'by_method': {}
    }

    for i, project in enumerate(python_projects):
        if (i + 1) % 5000 == 0:
            print("   Processed {i + 1:,}/{len(python_projects):,}...")

        is_on_pypi, confidence, method = checker.check_project(project)

        stats['total_checked'] += 1

        if is_on_pypi:
            stats['on_pypi'] += 1

            # Extract owner login (handle dict or string)
            owner = project.get('owner', '')
            if isinstance(owner, dict):
                owner = owner.get('login', '')

            # Store project info
            pypi_projects.append({
                'name': project.get('name'),
                'full_name': project.get('full_name'),
                'owner': owner,
                'stars': project.get('stars', 0),
                'description': project.get('description', ''),
                'url': project.get('url', ''),
                'topics': project.get('topics', []),
                'confidence': confidence,
                'match_method': method
            })

            # Update confidence stats
            if confidence > 0.9:
                stats['by_confidence']['very_high'] += 1
            elif confidence > 0.8:
                stats['by_confidence']['high'] += 1
            elif confidence > 0.7:
                stats['by_confidence']['medium'] += 1
            else:
                stats['by_confidence']['low'] += 1

            # Update method stats
            stats['by_method'][method] = stats['by_method'].get(method, 0) + 1
        else:
            stats['not_on_pypi'] += 1

    print("   Processed {len(python_projects):,}/{len(python_projects):,} ✓")

    # Sort by stars (most popular first)
    pypi_projects.sort(key=lambda x: x['stars'], reverse=True)

    # Output results
    output_file = 'data/seattle_pypi_projects.json'
    output_data = {
        'generated_at': data.get('collected_at', 'unknown'),
        'total_python_projects': len(python_projects),
        'projects_on_pypi': len(pypi_projects),
        'detection_rate': f"{len(pypi_projects) / len(python_projects) * 100:.2f}%",
        'statistics': stats,
        'projects': pypi_projects
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    print("\n✅ Generated {output_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)

    print("\n🐍 Python Projects:")
    print("   Total: {len(python_projects):,}")
    print("   On PyPI: {len(pypi_projects):,} ({len(pypi_projects) / len(python_projects) * 100:.2f}%)")
    print("   Not on PyPI: {stats['not_on_pypi']:,} ({stats['not_on_pypi'] / len(python_projects) * 100:.2f}%)")

    print("\n📈 Confidence Distribution:")
    print("   Very High (>0.9): {stats['by_confidence']['very_high']:,}")
    print("   High (0.8-0.9):   {stats['by_confidence']['high']:,}")
    print("   Medium (0.7-0.8): {stats['by_confidence']['medium']:,}")
    print("   Low (0.4-0.7):    {stats['by_confidence']['low']:,}")

    print("\n🔍 Top Match Methods:")
    for method, method_count in sorted(
        stats['by_method'].items(), key=lambda x: -x[1]
    )[:5]:
        percentage = method_count / len(pypi_projects) * 100
        print(f"   {method:<30} {method_count:,} ({percentage:.1f}%)")

    if pypi_projects:
        print("\n⭐ Top 10 Most Popular PyPI Packages:")
        for i, project in enumerate(pypi_projects[:10], 1):
            proj_stars = project['stars']
            proj_name = project['name']
            proj_owner = project['owner']
            print(f"   {i:2}. {proj_owner}/{proj_name:<30} {proj_stars:>6,} ⭐")

    print("\n" + "=" * 80)
    print("📁 Output saved to: {output_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()
