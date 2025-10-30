"""
Seattle Project Collector
Strategy: Find Seattle developers → Sort by followers/repos → Fetch their projects → Collect 10,000
"""
import os
import json
import time
import requests
from typing import List, Dict, Set
from tqdm import tqdm
from datetime import datetime


class SeattleProjectCollector:
    """Collect projects from Seattle-area developers"""
    
    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("❌ GitHub token required. Set GITHUB_TOKEN environment variable.")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def search_seattle_users(self, sort: str = "followers", max_users: int = 5000) -> List[Dict]:
        """
        Search for Seattle-area users
        
        Args:
            sort: Sort method (followers, repositories, joined)
            max_users: Maximum number of users to fetch
        """
        print(f"🔍 Searching for Seattle developers (sort: {sort})...")
        
        users = []
        page = 1
        per_page = 100
        
        # GitHub search API returns max 1000 results
        max_pages = min(10, (max_users + per_page - 1) // per_page)
        
        with tqdm(total=max_users, desc="Fetching users") as pbar:
            while page <= max_pages and len(users) < max_users:
                try:
                    url = f"https://api.github.com/search/users"
                    params = {
                        "q": "location:seattle",
                        "sort": sort,
                        "order": "desc",
                        "per_page": per_page,
                        "page": page
                    }
                    
                    response = self.session.get(url, params=params, timeout=30)
                    
                    if response.status_code == 403:
                        # Rate limit hit
                        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                        if reset_time:
                            wait_time = reset_time - time.time() + 5
                            if wait_time > 0:
                                print(f"\n⏳ Rate limit 達到,等待 {int(wait_time)} 秒...")
                                time.sleep(wait_time)
                                continue
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    items = data.get("items", [])
                    if not items:
                        break
                    
                    users.extend(items)
                    pbar.update(len(items))
                    page += 1
                    
                    # 避免過快請求
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"\n❌ Failed to fetch users (page {page}): {e}")
                    break
        
        print(f"✅ Found {len(users)}  Seattle developers")
        return users[:max_users]
    
    def get_user_repositories(self, username: str) -> List[Dict]:
        """Get all public repositories for a user"""
        repos = []
        page = 1
        per_page = 100
        
        while True:
            try:
                url = f"https://api.github.com/users/{username}/repos"
                params = {
                    "sort": "updated",
                    "per_page": per_page,
                    "page": page
                }
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 404:
                    # User does not exist or was deleted
                    break
                
                if response.status_code == 403:
                    # Rate limit
                    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                    if reset_time:
                        wait_time = reset_time - time.time() + 5
                        if wait_time > 0:
                            time.sleep(wait_time)
                            continue
                
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    break
                
                repos.extend(data)
                page += 1
                
                # 避免過快請求
                time.sleep(0.5)
                
            except Exception as e:
                print(f"\n⚠️  Fetching {username} 's repositories failed: {e}")
                break
        
        return repos
    
    def collect_projects(
        self,
        target_count: int = 10000,
        sort_users_by: str = "followers",
        output_file: str = "data/seattle_projects_10000.json"
    ) -> List[Dict]:
        """
        收集西雅圖開發者的專案
        
        Args:
            target_count: target專案數量
            sort_users_by: 用戶排序方式
            output_file: 輸出文件路徑
        """
        print(f"\n🚀 Starting Seattle project collection (target: {target_count} )")
        print("="*60)
        
        # 1. Fetching西雅圖開發者
        # 為了收集 10000 專案,估計需要 1000-2000 活躍用戶
        users = self.search_seattle_users(sort=sort_users_by, max_users=1000)
        
        if not users:
            print("❌ 未Found西雅圖開發者")
            return []
        
        # 2. Collecting projects
        print(f"\n📦 Starting project collection...")
        all_projects = []
        seen_repos = set()  # 去重(用 full_name)
        
        with tqdm(total=target_count, desc="Collecting projects") as pbar:
            for user in users:
                if len(all_projects) >= target_count:
                    break
                
                username = user["login"]
                
                # Fetching用戶的倉庫
                repos = self.get_user_repositories(username)
                
                for repo in repos:
                    if len(all_projects) >= target_count:
                        break
                    
                    # 去重
                    repo_full_name = repo["full_name"]
                    if repo_full_name in seen_repos:
                        continue
                    
                    seen_repos.add(repo_full_name)
                    
                    # 提取需要的信息
                    project = {
                        "name_with_owner": repo["full_name"],
                        "name": repo["name"],
                        "description": repo.get("description", ""),
                        "url": repo["html_url"],
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "watchers": repo["watchers_count"],
                        "open_issues": repo["open_issues_count"],
                        "created_at": repo["created_at"],
                        "updated_at": repo["updated_at"],
                        "pushed_at": repo.get("pushed_at", ""),
                        "language": repo.get("language", ""),
                        "license": repo.get("license", {}).get("spdx_id", "") if repo.get("license") else "",
                        "owner": {
                            "login": user["login"],
                            "type": user["type"],
                            "avatar_url": user.get("avatar_url", ""),
                        },
                        "is_fork": repo["fork"],
                        "is_archived": repo.get("archived", False),
                    }
                    
                    all_projects.append(project)
                    pbar.update(1)
        
        print(f"\n✅ Total collected {len(all_projects)} 專案")
        
        # 3. 按 stars 排序
        print(f"\n⭐ Sorting by stars...")
        all_projects.sort(key=lambda x: x["stars"], reverse=True)
        
        # 4. Statistics
        self._print_statistics(all_projects)
        
        # 5. 保存數據
        print(f"\n💾 Saving data to: {output_file}")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_projects, f, indent=2, ensure_ascii=False)
        
        # 同時保存元數據
        metadata = {
            "collection_time": datetime.now().isoformat(),
            "total_projects": len(all_projects),
            "total_users": len(users),
            "sort_users_by": sort_users_by,
            "target_count": target_count,
        }
        
        metadata_file = output_file.replace(".json", "_metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Metadata saved to: {metadata_file}")
        print(f"\n✅ Complete! Ready for analysis.")
        
        return all_projects
    
    def _print_statistics(self, projects: List[Dict]):
        """打印Statistics"""
        print(f"\n📊 Statistics:")
        print(f"   Total projects: {len(projects)}")
        
        # Language distribution
        languages = {}
        for proj in projects:
            lang = proj.get("language") or "Unknown"
            languages[lang] = languages.get(lang, 0) + 1
        
        print(f"\n🔤 Language distribution (top 15):")
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        for lang, count in sorted_langs[:15]:
            print(f"   {lang:20s}: {count:5d} 專案 ({count/len(projects)*100:.1f}%)")
        
        # Star distribution
        star_ranges = {
            '10000+': 0,
            '5000-9999': 0,
            '1000-4999': 0,
            '500-999': 0,
            '100-499': 0,
            '50-99': 0,
            '10-49': 0,
            '1-9': 0,
            '0': 0
        }
        
        for proj in projects:
            stars = proj.get("stars", 0)
            if stars >= 10000:
                star_ranges['10000+'] += 1
            elif stars >= 5000:
                star_ranges['5000-9999'] += 1
            elif stars >= 1000:
                star_ranges['1000-4999'] += 1
            elif stars >= 500:
                star_ranges['500-999'] += 1
            elif stars >= 100:
                star_ranges['100-499'] += 1
            elif stars >= 50:
                star_ranges['50-99'] += 1
            elif stars >= 10:
                star_ranges['10-49'] += 1
            elif stars >= 1:
                star_ranges['1-9'] += 1
            else:
                star_ranges['0'] += 1
        
        print(f"\n⭐ Star distribution:")
        for range_name, count in star_ranges.items():
            if count > 0:
                print(f"   {range_name:15s}: {count:5d} 專案 ({count/len(projects)*100:.1f}%)")
        
        # top 20 最受歡迎的專案
        print(f"\n🏆 top 20 最受歡迎的專案:")
        for i, proj in enumerate(projects[:20], 1):
            print(f"   {i:2d}. {proj['name_with_owner']:50s} {proj['stars']:7d} ⭐ ({proj.get('language', 'N/A')})")


def main():
    """Main function"""
    collector = SeattleProjectCollector()
    
    # 收集 10000 專案
    projects = collector.collect_projects(
        target_count=10000,
        sort_users_by="followers",  # or "repositories"
        output_file="data/seattle_projects_10000.json"
    )
    
    print(f"\n✅ Successfully collected {len(projects)} 西雅圖專案!")


if __name__ == "__main__":
    main()
