#!/usr/bin/env python3
"""
Test PyPI client with real data
"""
from pypi_client import PyPIClient

def test_pypi_client():
    client = PyPIClient()
    
    # Test cases: repo names to test
    test_repos = [
        "donnemartin/system-design-primer",  # Python repo
        "pytorch/pytorch",  # Should map to 'torch'
        "scikit-learn/scikit-learn",  # Direct match
        "pallets/flask",  # Flask package
        "psf/requests",  # Requests package
        "microsoft/vscode",  # Not a Python package
    ]
    
    print("🧪 Testing PyPI Client\n")
    print("=" * 80)
    
    for repo_name in test_repos:
        print(f"\n📦 Repo: {repo_name}")
        info = client.get_package_info(repo_name)
        
        print(f"   Package: {info['package_name']}")
        print(f"   Exists: {info['exists']}")
        if info['exists']:
            downloads = info['downloads_month']
            print(f"   Downloads (month): {downloads:,}" if downloads else "   Downloads: N/A")
        print("-" * 80)

if __name__ == "__main__":
    test_pypi_client()
