#!/usr/bin/env python3
"""
PyPI Package Checker - Check if GitHub projects are on PyPI
Uses offline matching for high performance
"""
import json
import requests
from pathlib import Path
from typing import Set, Dict, Optional, List, Tuple
import re
import time


class PyPIChecker:
    """Check if projects are on PyPI using local database"""
    
    # Manual mappings for known difficult cases
    MANUAL_MAPPINGS = {
        'beautiful-soup': 'beautifulsoup4',
        'beautifulsoup': 'beautifulsoup4',
        'pillow': 'pillow',
        'pyyaml': 'pyyaml',
        'python-dateutil': 'python-dateutil',
        'pytorch': 'torch',
        'tensorflow': 'tensorflow',
        'scikit-learn': 'scikit-learn',
        'opencv-python': 'opencv-python',
        'opencv': 'opencv-python',
        'playwright-python': 'playwright',
        'msgpack-python': 'msgpack',
        'protobuf': 'protobuf',
        'python-telegram-bot': 'python-telegram-bot',
    }
    
    # Patterns that indicate NOT a package
    EXCLUDE_PATTERNS = [
        r'^awesome-',
        r'^learn-',
        r'^tutorial-',
        r'-tutorial$',
        r'-example$',
        r'-examples$',
        r'-demo$',
        r'-demos$',
        r'dotfiles',
        r'-homework$',
        r'-assignment$',
        r'^test-',
        r'-test$',
        r'playground',
        r'sandbox',
    ]
    
    # Additional exclude patterns for common false positives
    # These are generic names that might match real PyPI packages but are unlikely to be the repo
    GENERIC_NAMES = [
        'app', 'demo', 'test', 'example', 'sample', 'template',
        'project', 'chat', 'bot', 'tool', 'utils', 'helpers',
        'api', 'server', 'client', 'backend', 'frontend',
    ]
    
    def __init__(self, cache_dir: str = 'data'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pypi_packages: Set[str] = set()
        self.load_or_download_index()
    
    def download_pypi_simple_index(self) -> Set[str]:
        """Download complete PyPI package list from Simple API"""
        print("📥 Downloading PyPI package index...")
        try:
            response = requests.get('https://pypi.org/simple/', timeout=30)
            response.raise_for_status()
            
            # Parse HTML links to extract package names
            # PyPI Simple API format: <a href="/simple/package-name/">package-name</a>
            packages = set()
            import re
            for match in re.finditer(r'<a[^>]*>([^<]+)</a>', response.text):
                package_name = match.group(1).strip().lower()  # Normalize to lowercase
                if package_name:
                    packages.add(package_name)
            
            print(f"✅ Found {len(packages):,} packages on PyPI")
            return packages
        except Exception as e:
            print(f"❌ Failed to download PyPI index: {e}")
            return set()
    
    def load_or_download_index(self):
        """Load cached index or download new one"""
        cache_file = self.cache_dir / 'pypi_official_packages.json'
        
        # Check if cache exists and is recent (< 7 days)
        if cache_file.exists():
            age_days = (time.time() - cache_file.stat().st_mtime) / 86400
            
            if age_days < 7:
                print(f"📦 Loading PyPI cache ({age_days:.1f} days old)")
                with open(cache_file) as f:
                    self.pypi_packages = set(json.load(f))
                print(f"   Loaded {len(self.pypi_packages):,} packages")
                return
        
        # Download new index
        self.pypi_packages = self.download_pypi_simple_index()
        
        if self.pypi_packages:
            # Save to cache
            with open(cache_file, 'w') as f:
                json.dump(sorted(self.pypi_packages), f)
            print(f"💾 Saved cache to {cache_file}")
    
    def check_project(self, repo: Dict) -> Tuple[bool, float, str]:
        """
        Check if a project is on PyPI with STRICT matching to avoid false positives
        
        Returns:
            (is_on_pypi, confidence_score, match_method)
        """
        repo_name = repo.get('name', '').lower()
        
        if not repo_name:
            return (False, 0.0, 'no_name')
        
        # 1. Check exclude patterns first
        for pattern in self.EXCLUDE_PATTERNS:
            if re.search(pattern, repo_name):
                return (False, 0.0, 'excluded_pattern')
        
        # 2. Check manual mappings (highest confidence)
        if repo_name in self.MANUAL_MAPPINGS:
            mapped_name = self.MANUAL_MAPPINGS[repo_name].lower()
            if mapped_name in self.pypi_packages:
                return (True, 0.95, 'manual_mapping')
        
        # 3. Direct match (high confidence)
        if repo_name in self.pypi_packages:
            # But exclude if it's a generic name without strong signals
            if self._has_strong_pypi_signals(repo):
                return (True, 0.95, 'direct_match_verified')
            elif repo_name not in self.GENERIC_NAMES:
                return (True, 0.90, 'direct_match')
            else:
                # Generic name - need strong signals
                return (False, 0.0, 'generic_name_excluded')
        
        # 4. Underscore/hyphen conversion (medium confidence)
        dash_to_underscore = repo_name.replace('-', '_')
        if dash_to_underscore in self.pypi_packages and dash_to_underscore not in self.GENERIC_NAMES:
            if self._has_strong_pypi_signals(repo):
                return (True, 0.90, 'dash_to_underscore_verified')
            else:
                return (True, 0.85, 'dash_to_underscore')
        
        underscore_to_dash = repo_name.replace('_', '-')
        if underscore_to_dash in self.pypi_packages and underscore_to_dash not in self.GENERIC_NAMES:
            if self._has_strong_pypi_signals(repo):
                return (True, 0.90, 'underscore_to_dash_verified')
            else:
                return (True, 0.85, 'underscore_to_dash')
        
        # 5. Remove common prefixes (lower confidence - STRICT)
        # Only if we have strong signals OR the cleaned name is specific enough
        prefixes = ['python-', 'py-', 'django-', 'flask-', 'pytest-']
        for prefix in prefixes:
            if repo_name.startswith(prefix):
                clean_name = repo_name[len(prefix):]
                
                # Reject if cleaned name is too short or generic
                if len(clean_name) < 4 or clean_name in self.GENERIC_NAMES:
                    continue
                
                if clean_name in self.pypi_packages:
                    # REQUIRE strong signals for prefix removal matches
                    if self._has_strong_pypi_signals(repo):
                        return (True, 0.80, f'removed_prefix_{prefix}_verified')
                    # Otherwise, skip this match to avoid false positives
                
                # Also try underscore version
                clean_underscore = clean_name.replace('-', '_')
                if clean_underscore in self.pypi_packages and len(clean_underscore) >= 4:
                    if self._has_strong_pypi_signals(repo):
                        return (True, 0.75, f'removed_prefix_{prefix}_underscore_verified')
        
        # 6. Check for VERY strong signals only
        # Only mark as on_pypi if we have explicit mentions
        if self._has_very_strong_pypi_signals(repo):
            return (True, 0.70, 'very_strong_signals')
        
        return (False, 0.0, 'no_match')
    
    def _has_strong_pypi_signals(self, repo: Dict) -> bool:
        """Check if repo has strong signals of being a PyPI package"""
        # Check topics
        topics = repo.get('topics', [])
        if any(t in topics for t in ['pypi', 'python-package', 'pip', 'setuptools']):
            return True
        
        # Check description
        description = (repo.get('description') or '').lower()
        if any(keyword in description for keyword in ['pip install', 'pypi.org', 'pypi package']):
            return True
        
        # Check README content if available
        readme = (repo.get('readme') or '').lower()
        if readme:
            if 'pip install' in readme and repo.get('name', '').lower() in readme:
                return True
            if 'pypi.org/project/' in readme:
                return True
        
        return False
    
    def _has_very_strong_pypi_signals(self, repo: Dict) -> bool:
        """Check if repo has VERY strong signals - only for high confidence without name match"""
        readme = (repo.get('readme') or '').lower()
        repo_name = repo.get('name', '').lower()
        
        # Must have explicit pip install command with the package name
        if f'pip install {repo_name}' in readme:
            return True
        
        # Or explicit PyPI link
        if f'pypi.org/project/{repo_name}' in readme:
            return True
        
        return False
    
    def batch_check(self, repos: List[Dict], fetch_readme: bool = False, github_token: Optional[str] = None) -> List[Dict]:
        """
        Batch check multiple repos (very fast, all local)
        
        Args:
            repos: List of repository dictionaries
            fetch_readme: If True, fetch README from GitHub for better accuracy (slower)
            github_token: GitHub token for API access (if fetch_readme=True)
        """
        print(f"🔍 Checking {len(repos):,} projects against PyPI...")
        
        if fetch_readme and github_token:
            print("   Fetching README files from GitHub for higher accuracy...")
            self._fetch_readmes(repos, github_token)
        
        results = []
        for repo in repos:
            is_on_pypi, confidence, method = self.check_project(repo)
            repo['on_pypi'] = is_on_pypi
            repo['pypi_confidence'] = confidence
            repo['pypi_match_method'] = method
            results.append(repo)
        
        on_pypi = sum(1 for r in results if r.get('on_pypi'))
        print(f"✅ Found {on_pypi:,} projects on PyPI ({on_pypi/len(results)*100:.1f}%)")
        
        return results
    
    def _fetch_readmes(self, repos: List[Dict], github_token: str):
        """Fetch README files from GitHub API for better matching"""
        import requests
        
        headers = {'Authorization': f'token {github_token}'}
        
        for i, repo in enumerate(repos):
            if i % 100 == 0:
                print(f"   Fetched {i}/{len(repos)} READMEs...")
            
            owner = repo.get('owner', {}).get('login') if isinstance(repo.get('owner'), dict) else repo.get('owner')
            name = repo.get('name')
            
            if not owner or not name:
                continue
            
            try:
                # Get README via API
                url = f'https://api.github.com/repos/{owner}/{name}/readme'
                resp = requests.get(url, headers=headers, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    # Decode base64 content
                    import base64
                    content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
                    repo['readme'] = content.lower()
            except Exception:
                pass  # Skip on error


def main():
    """Test the PyPI checker"""
    print("🧪 Testing PyPI Checker\n")
    
    checker = PyPIChecker()
    
    # Test some examples
    test_projects = [
        {'name': 'requests', 'description': 'HTTP library'},
        {'name': 'flask', 'description': 'Web framework'},
        {'name': 'my-random-project', 'description': 'Random stuff'},
    ]
    
    for project in test_projects:
        is_on_pypi, confidence, method = checker.check_project(project)
        status = "✅" if is_on_pypi else "❌"
        print(f"{status} {project['name']}: {is_on_pypi} (confidence: {confidence:.2f}, method: {method})")


if __name__ == '__main__':
    main()
