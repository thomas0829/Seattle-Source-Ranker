#!/usr/bin/env python3
"""
Update top PyPI packages ranking from remote GitHub repository.

This script downloads the latest top_pypi_packages.json from a GitHub repository
and updates the local copy if the remote version is newer.
"""

import json
import urllib.request
import sys
from pathlib import Path
from datetime import datetime


# GitHub raw content URL for top_pypi_packages.json
# Update this URL to point to your source repository
GITHUB_RAW_URL = "https://raw.githubusercontent.com/hugovk/top-pypi-packages/main/top-pypi-packages-30-days.json"


def get_local_last_update(data_dir: Path) -> str:
    """Get the last_update timestamp from local file."""
    local_file = data_dir / "top_pypi_packages.json"
    
    if not local_file.exists():
        return None
    
    try:
        with open(local_file, 'r') as f:
            data = json.load(f)
        return data.get('last_update')
    except Exception as e:
        print(f"⚠️  Failed to read local file: {e}")
        return None


def download_remote_data(url: str) -> dict:
    """Download top PyPI packages data from remote URL."""
    print(f"📥 Downloading from: {url}")
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read())
        return data
    except Exception as e:
        print(f"❌ Failed to download: {e}")
        return None


def save_data(data: dict, data_dir: Path):
    """Save data to local file."""
    output_file = data_dir / "top_pypi_packages.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to: {output_file}")


def main():
    # Determine project root (parent of scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    
    print("=" * 80)
    print("UPDATE TOP PYPI PACKAGES RANKING")
    print("=" * 80)
    
    # Get local version timestamp
    local_update = get_local_last_update(data_dir)
    if local_update:
        print(f"📂 Local version: {local_update}")
    else:
        print("📂 Local version: Not found")
    
    # Download remote version
    remote_data = download_remote_data(GITHUB_RAW_URL)
    if not remote_data:
        print("❌ Update failed - could not download remote data")
        sys.exit(1)
    
    remote_update = remote_data.get('last_update')
    print(f"🌐 Remote version: {remote_update}")
    
    # Check if update is needed
    if local_update and local_update == remote_update:
        print("✅ Already up to date - no update needed")
        sys.exit(0)
    
    # Update local file
    print(f"\n🔄 Updating from {local_update or 'None'} → {remote_update}")
    save_data(remote_data, data_dir)
    
    # Show statistics
    total_packages = remote_data.get('total_rows', 0)
    print(f"\n📊 Total packages: {total_packages:,}")
    print(f"📅 Last update: {remote_update}")
    print("\n✅ Update completed successfully!")


if __name__ == "__main__":
    main()
