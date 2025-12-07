#!/usr/bin/env python3
"""
Update PyPI official package index (daily).

Downloads the complete list of packages from PyPI Simple Index.
This is used for checking if Seattle projects are published on PyPI.
"""

import json
import re
import sys
from pathlib import Path
import requests


def download_pypi_simple_index() -> set:
    """Download complete package list from PyPI Simple Index"""
    url = "https://pypi.org/simple/"
    print(f"[DOWNLOAD] PyPI Simple Index from: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Extract package names from HTML
        packages = set()
        for match in re.finditer(r'<a[^>]*>([^<]+)</a>', response.text):
            package_name = match.group(1).strip().lower()
            if package_name:
                packages.add(package_name)
        
        print(f"[OK] Downloaded {len(packages):,} packages")
        return packages
        
    except requests.RequestException as e:
        print(f"[ERROR] Failed to download: {e}")
        return None


def save_index(packages: set, data_dir: Path):
    """Save package index to file"""
    output_file = data_dir / "pypi_official_packages.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted(packages), f, indent=2, ensure_ascii=False)
    
    print(f"[SAVE] Saved to: {output_file}")


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    
    print("=" * 80)
    print("UPDATE PYPI OFFICIAL PACKAGE INDEX")
    print("=" * 80)
    
    # Download index
    packages = download_pypi_simple_index()
    if not packages:
        print("[ERROR] Update failed")
        sys.exit(1)
    
    # Save to file
    save_index(packages, data_dir)
    
    print("\n[OK] Update completed successfully!")
    print(f"[INFO] Total packages: {len(packages):,}")


if __name__ == "__main__":
    main()
