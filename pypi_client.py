"""
PyPI API Client for fetching package download statistics
"""
import requests
from typing import Optional, Dict

class PyPIClient:
    def __init__(self):
        self.pypistats_api = "https://pypistats.org/api/packages"
        self.pypi_api = "https://pypi.org/pypi"
        
        # Common mappings for repos that have different PyPI names
        self.name_mappings = {
            "pytorch": "torch",
            "pytorch/pytorch": "torch",
            "scikit-learn": "scikit-learn",
            "opencv": "opencv-python",
            "opencv/opencv-python": "opencv-python",
            "pillow": "Pillow",
            "python-pillow/pillow": "Pillow",
            "beautifulsoup": "beautifulsoup4",
            "pyyaml": "PyYAML",
            "yaml/pyyaml": "PyYAML",
            "psf/requests": "requests",
            "pallets/flask": "flask",
            "django/django": "django",
            "numpy/numpy": "numpy",
            "pandas-dev/pandas": "pandas",
            "tensorflow/tensorflow": "tensorflow",
            "keras-team/keras": "keras",
            "scipy/scipy": "scipy",
            "matplotlib/matplotlib": "matplotlib",
            "ipython/ipython": "ipython",
            "jupyter/notebook": "notebook",
            "python/cpython": None,  # CPython itself, not a package
            "system-design-primer": None,  # Learning resources, not packages
            "generative-ai-for-beginners": None,
            "ml-for-beginners": None,
            "ai-for-beginners": None,
        }
    
    def get_package_name(self, repo_name: str) -> str:
        """
        Try to find the correct PyPI package name from repo name
        Returns None if the repo is known to not be a package
        """
        # Extract package name from repo (remove owner)
        if '/' in repo_name:
            original_name = repo_name
            repo_name = repo_name.split('/')[-1]
        else:
            original_name = repo_name
        
        repo_lower = repo_name.lower()
        original_lower = original_name.lower()
        
        # Check mappings first (both full name and repo name)
        if original_lower in self.name_mappings:
            return self.name_mappings[original_lower]
        
        if repo_lower in self.name_mappings:
            return self.name_mappings[repo_lower]
        
        # Try exact match
        return repo_name
    
    def package_exists(self, package_name: str) -> bool:
        """
        Check if a package exists on PyPI
        """
        try:
            url = f"{self.pypi_api}/{package_name}/json"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_recent_downloads(self, package_name: str, period: str = "month") -> Optional[int]:
        """
        Get recent download count from PyPI Stats
        period: 'day', 'week', or 'month'
        """
        try:
            url = f"{self.pypistats_api}/{package_name}/recent"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Get downloads for the specified period
                if 'data' in data and period in data['data']:
                    return data['data'][period]
                # Fallback to last_month if available
                elif 'data' in data and 'last_month' in data['data']:
                    return data['data']['last_month']
            
            return None
        except Exception as e:
            print(f"  ⚠️ Failed to fetch PyPI stats for {package_name}: {e}")
            return None
    
    def get_package_info(self, repo_name: str) -> Dict:
        """
        Get comprehensive package information
        Returns: dict with package_name, downloads, exists
        """
        package_name = self.get_package_name(repo_name)
        
        # If mapping returns None, it's known to not be a package
        if package_name is None:
            return {
                "package_name": None,
                "exists": False,
                "downloads_month": 0,
                "reason": "not_a_package"
            }
        
        # Check if package exists
        if not self.package_exists(package_name):
            return {
                "package_name": package_name,
                "exists": False,
                "downloads_month": 0,
                "reason": "not_found"
            }
        
        # Get download stats
        downloads = self.get_recent_downloads(package_name, "month")
        
        return {
            "package_name": package_name,
            "exists": True,
            "downloads_month": downloads or 0,
            "reason": "success"
        }
