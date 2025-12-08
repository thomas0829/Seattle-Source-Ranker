#!/usr/bin/env python3
"""
Verify which Seattle projects are the actual publishers on PyPI.

This script checks PyPI metadata to find the true GitHub repository URL
for each package, filtering out false matches where repo names coincidentally
match package names but aren't the actual publishers.
"""

import json
import urllib.request
import time
from pathlib import Path
from typing import Dict, List, Optional


def get_pypi_metadata(package_name: str) -> Optional[Dict]:
    """Fetch package metadata from PyPI JSON API."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"  ⚠️  Failed to fetch {package_name}: {e}")
        return None


def extract_github_repo(pypi_data: Dict) -> Optional[str]:
    """Extract GitHub repo URL from PyPI metadata."""
    if not pypi_data:
        return None
    
    info = pypi_data.get('info', {})
    
    # Check project_urls first
    project_urls = info.get('project_urls', {})
    if project_urls:
        for key in ['Source', 'Source Code', 'Repository', 'Homepage', 'Code']:
            url = project_urls.get(key, '')
            if 'github.com' in url.lower():
                return normalize_github_url(url)
    
    # Check home_page
    home_page = info.get('home_page', '')
    if home_page and 'github.com' in home_page.lower():
        return normalize_github_url(home_page)
    
    # Check package_url
    package_url = info.get('package_url', '')
    if package_url and 'github.com' in package_url.lower():
        return normalize_github_url(package_url)
    
    return None


def normalize_github_url(url: str) -> str:
    """Normalize GitHub URL to owner/repo format."""
    url = url.lower().strip()
    
    # Remove protocol
    url = url.replace('https://', '').replace('http://', '')
    url = url.replace('www.', '')
    
    # Extract github.com/owner/repo
    if 'github.com/' in url:
        parts = url.split('github.com/')[1].split('/')
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1].rstrip('.git')
            return f"{owner}/{repo}"
    
    return url


def verify_matches(matched_projects: List[Dict]) -> Dict:
    """Verify which projects are true PyPI publishers."""
    verified = []
    false_positives = []
    no_github_link = []
    
    total = len(matched_projects)
    
    print(f"\n🔍 Verifying {total} matched projects...")
    print("=" * 80)
    
    for i, project in enumerate(matched_projects, 1):
        package_name = project['pypi_package']
        seattle_repo = f"{project['owner']}/{project['repo']}".lower()
        
        print(f"\n[{i}/{total}] Checking {package_name}...")
        
        # Fetch PyPI metadata
        pypi_data = get_pypi_metadata(package_name)
        if not pypi_data:
            false_positives.append({
                **project,
                'verification_status': 'pypi_fetch_failed'
            })
            continue
        
        # Extract GitHub repo from PyPI
        pypi_github = extract_github_repo(pypi_data)
        
        if not pypi_github:
            print(f"  ℹ️  No GitHub link in PyPI metadata")
            no_github_link.append({
                **project,
                'verification_status': 'no_github_link',
                'pypi_github': None
            })
            continue
        
        # Compare repos (case-insensitive)
        if seattle_repo == pypi_github.lower():
            print(f"  ✅ VERIFIED: {seattle_repo} == {pypi_github}")
            verified.append({
                **project,
                'verification_status': 'verified',
                'pypi_github': pypi_github
            })
        else:
            print(f"  ❌ MISMATCH: {seattle_repo} != {pypi_github}")
            false_positives.append({
                **project,
                'verification_status': 'mismatch',
                'pypi_github': pypi_github
            })
        
        # Rate limiting
        if i % 10 == 0:
            time.sleep(1)
    
    return {
        'verified': verified,
        'false_positives': false_positives,
        'no_github_link': no_github_link
    }


def print_summary(results: Dict):
    """Print verification summary."""
    verified = results['verified']
    false_positives = results['false_positives']
    no_github_link = results['no_github_link']
    
    total = len(verified) + len(false_positives) + len(no_github_link)
    
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"\nTotal checked: {total}")
    print(f"✅ Verified (True owners):     {len(verified):4} ({len(verified)/total*100:.1f}%)")
    print(f"❌ False positives (Mismatches): {len(false_positives):4} ({len(false_positives)/total*100:.1f}%)")
    print(f"ℹ️  No GitHub link:           {len(no_github_link):4} ({len(no_github_link)/total*100:.1f}%)")
    
    if verified:
        print("\n" + "=" * 80)
        print("✅ VERIFIED SEATTLE PYPI PUBLISHERS")
        print("=" * 80)
        
        # Sort by downloads
        verified_sorted = sorted(verified, key=lambda x: x['pypi_downloads'], reverse=True)
        
        for proj in verified_sorted:
            owner = proj['owner']
            repo = proj['repo']
            stars = proj['stars']
            downloads = proj['pypi_downloads']
            rank = proj['pypi_rank']
            print(f"\n  {owner}/{repo}")
            print(f"    ⭐ Stars: {stars:,}")
            print(f"    📥 Downloads: {downloads:,}/month")
            print(f"    🏆 PyPI Rank: #{rank:,}")
    
    if false_positives:
        print("\n" + "=" * 80)
        print("❌ FALSE POSITIVES (repo name coincidence)")
        print("="*80)
        print("\nExamples (first 10):")
        for proj in false_positives[:10]:
            seattle = f"{proj['owner']}/{proj['repo']}"
            actual = proj.get('pypi_github', 'unknown')
            package = proj['pypi_package']
            print(f"  • {package}: {seattle} (actual: {actual})")


def save_verified_results(results: Dict, output_dir: Path):
    """Save verified results to standard JSON file."""
    from datetime import datetime
    
    # Use standard filename - overwrite existing
    output_file = output_dir / "seattle_top_pypi_matches.json"
    with open(output_file, 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'statistics': {
                'total_verified': len(results['verified']),
                'false_positives': len(results['false_positives']),
                'no_github_link': len(results['no_github_link'])
            },
            'matched_projects': results['verified']  # Only save verified ones
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Updated: {output_file} (kept only verified projects)")


def main():
    """Main execution."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    
    # Load standard match file
    match_file = data_dir / "seattle_top_pypi_matches.json"
    if not match_file.exists():
        print("❌ seattle_top_pypi_matches.json not found. Run extract_top_pypi_matches.py first.")
        return
    
    print(f"Loading matches from: {match_file}")
    
    with open(match_file, 'r') as f:
        data = json.load(f)
    
    matched_projects = data['matched_projects']
    
    # Verify matches
    results = verify_matches(matched_projects)
    
    # Print summary
    print_summary(results)
    
    # Save results
    save_verified_results(results, data_dir)
    
    print("\n" + "=" * 80)
    print("✓ Verification complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
