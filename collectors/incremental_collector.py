"""
Incremental Project Collector
- Preserve existing projects, avoid duplicate fetching
- Support incremental updates (only update changed projects)
- Smart replacement (replace low-scored projects with better ones)
"""
import os
import json
import time
import requests
from typing import List, Dict, Set, Optional
from datetime import datetime, timedelta
from tqdm import tqdm


class IncrementalProjectCollector:
    """Incremental Project Collector - Smart project pool management"""
    
    def __init__(self, token: str = None, data_file: str = "data/seattle_projects_10000.json"):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("❌ GitHub token required")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        self.data_file = data_file
        self.backup_file = data_file.replace(".json", "_backup.json")
        
        # 加載現有數據
        self.existing_projects = self._load_existing_projects()
        self.existing_repos = {p["name_with_owner"]: p for p in self.existing_projects}
        
        print(f"📦 Loaded {len(self.existing_projects)}  existing projects")
    
    def _load_existing_projects(self) -> List[Dict]:
        """Load existing project data"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✅ Found existing data file: {self.data_file}")
                    return data
            except Exception as e:
                print(f"⚠️  Failed to load existing data: {e}")
                return []
        else:
            print(f"ℹ️  未Found existing data file,將創建新的")
            return []
    
    def _save_projects(self, projects: List[Dict], backup: bool = True):
        """Save project data (with backup)"""
        # 備份舊數據
        if backup and os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    old_data = f.read()
                with open(self.backup_file, 'w') as f:
                    f.write(old_data)
                print(f"💾 Backup old data to: {self.backup_file}")
            except Exception as e:
                print(f"⚠️  Backup failed: {e}")
        
        # 保存新數據
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)
        
        # 保存元數據
        metadata = {
            "last_updated": datetime.now().isoformat(),
            "total_projects": len(projects),
            "data_file": self.data_file,
        }
        metadata_file = self.data_file.replace(".json", "_metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def update_project_stats(self, project_name: str) -> Optional[Dict]:
        """Update statistics for single project(stars, forks 等)"""
        try:
            url = f"https://api.github.com/repos/{project_name}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 404:
                print(f"⚠️  Project does not exist: {project_name}")
                return None
            
            if response.status_code == 403:
                # Rate limit
                print(f"⚠️  Rate limit  hit, pausing updates")
                return None
            
            response.raise_for_status()
            repo = response.json()
            
            # 提取Updating的信息
            updated_project = {
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
                "owner": repo["owner"],
                "is_fork": repo["fork"],
                "is_archived": repo.get("archived", False),
                "last_stats_update": datetime.now().isoformat(),
            }
            
            return updated_project
            
        except Exception as e:
            print(f"⚠️  Updating {project_name} failed: {e}")
            return None
    
    def refresh_stale_projects(self, days_old: int = 7) -> int:
        """
        Refresh stale project data
        
        Args:
            days_old: 超過多少天未Updating的專案需要Refresh
        
        Returns:
            Refresh的專案數量
        """
        print(f"\n🔄 Refreshing projects older than {days_old} 天未Updating的專案...")
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        stale_projects = []
        
        for project in self.existing_projects:
            last_update = project.get("last_stats_update")
            if not last_update:
                stale_projects.append(project)
            else:
                update_date = datetime.fromisoformat(last_update)
                if update_date < cutoff_date:
                    stale_projects.append(project)
        
        print(f"📊 Found {len(stale_projects)} 個需要Updating的專案")
        
        if not stale_projects:
            print("✅ All projects are up to date!")
            return 0
        
        updated_count = 0
        with tqdm(total=len(stale_projects), desc="Updating專案") as pbar:
            for project in stale_projects:
                project_name = project["name_with_owner"]
                updated = self.update_project_stats(project_name)
                
                if updated:
                    # Updating現有專案
                    self.existing_repos[project_name] = updated
                    updated_count += 1
                
                pbar.update(1)
                time.sleep(0.5)  # 避免 rate limit
        
        # 重新生成專案列表並排序
        self.existing_projects = list(self.existing_repos.values())
        self.existing_projects.sort(key=lambda x: x["stars"], reverse=True)
        
        # 保存Updating後的數據
        self._save_projects(self.existing_projects)
        
        print(f"✅ 成功Updating {updated_count} 個專案")
        return updated_count
    
    def add_new_projects(
        self,
        new_projects: List[Dict],
        max_total: int = 10000,
        replace_strategy: str = "lowest_stars"
    ) -> Dict[str, int]:
        """
        Add new projects to pool
        
        Args:
            new_projects: 新Found的專案列表
            max_total: Maximum number of projects
            replace_strategy: Replacement strategy (lowest_stars, oldest, lowest_activity)
        
        Returns:
            Statistics {added, replaced, skipped}
        """
        print(f"\n➕ Processing {len(new_projects)}  new projects...")
        
        stats = {"added": 0, "replaced": 0, "skipped": 0, "updated": 0}
        
        for new_proj in new_projects:
            proj_name = new_proj["name_with_owner"]
            
            # 檢查是否已存在
            if proj_name in self.existing_repos:
                # Updating現有專案數據
                old_proj = self.existing_repos[proj_name]
                if new_proj["stars"] != old_proj["stars"]:
                    self.existing_repos[proj_name] = new_proj
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1
                continue
            
            # 如果未達到上限,直接添加
            if len(self.existing_projects) < max_total:
                self.existing_repos[proj_name] = new_proj
                self.existing_projects.append(new_proj)
                stats["added"] += 1
            else:
                # 已達上限,判斷是否Replaced
                if self._should_replace(new_proj, replace_strategy):
                    # 找到要被Replaced的專案
                    to_replace = self._find_project_to_replace(replace_strategy)
                    if to_replace:
                        # 執行Replaced
                        del self.existing_repos[to_replace["name_with_owner"]]
                        self.existing_repos[proj_name] = new_proj
                        self.existing_projects.remove(to_replace)
                        self.existing_projects.append(new_proj)
                        stats["replaced"] += 1
                        print(f"🔄 Replaced: {to_replace['name_with_owner']} ({to_replace['stars']}⭐) → {proj_name} ({new_proj['stars']}⭐)")
                else:
                    stats["skipped"] += 1
        
        # 重新排序
        self.existing_projects.sort(key=lambda x: x["stars"], reverse=True)
        
        # 保存Updating後的數據
        self._save_projects(self.existing_projects)
        
        print(f"\n📊 Processing結果:")
        print(f"   ➕ Added: {stats['added']}")
        print(f"   🔄 Replaced: {stats['replaced']}")
        print(f"   🔁 Updating: {stats['updated']}")
        print(f"   ⏭️  Skipped: {stats['skipped']}")
        
        return stats
    
    def _should_replace(self, new_project: Dict, strategy: str) -> bool:
        """判斷新專案是否應該Replaced現有專案"""
        if strategy == "lowest_stars":
            # 找Lowest stars 的專案
            lowest = min(self.existing_projects, key=lambda x: x["stars"])
            return new_project["stars"] > lowest["stars"]
        
        elif strategy == "oldest":
            # 找最舊的專案(最久沒Updating)
            oldest = min(self.existing_projects, key=lambda x: x.get("updated_at", ""))
            return new_project.get("updated_at", "") > oldest.get("updated_at", "")
        
        elif strategy == "lowest_activity":
            # 找活躍度Lowest的(stars + forks + watchers)
            def activity_score(p):
                return p.get("stars", 0) + p.get("forks", 0) + p.get("watchers", 0)
            
            lowest_activity = min(self.existing_projects, key=activity_score)
            return activity_score(new_project) > activity_score(lowest_activity)
        
        return False
    
    def _find_project_to_replace(self, strategy: str) -> Optional[Dict]:
        """找到應該被Replaced的專案"""
        if not self.existing_projects:
            return None
        
        if strategy == "lowest_stars":
            return min(self.existing_projects, key=lambda x: x["stars"])
        
        elif strategy == "oldest":
            return min(self.existing_projects, key=lambda x: x.get("updated_at", ""))
        
        elif strategy == "lowest_activity":
            def activity_score(p):
                return p.get("stars", 0) + p.get("forks", 0) + p.get("watchers", 0)
            return min(self.existing_projects, key=activity_score)
        
        return None
    
    def collect_with_smart_update(
        self,
        target_count: int = 10000,
        refresh_days: int = 7,
        collect_new: bool = True
    ):
        """
        智能Updating專案池
        
        Args:
            target_count: Target project count
            refresh_days: Refreshing projects older than多少天的專案
            collect_new: Whether to collect new projects
        """
        print(f"\n🚀 智能Updating專案池")
        print("="*60)
        
        # 步驟 1: Refresh過時專案
        self.refresh_stale_projects(days_old=refresh_days)
        
        # 步驟 2: 如果需要,Collecting new projects
        if collect_new and len(self.existing_projects) < target_count:
            print(f"\n📦 Current projects: {len(self.existing_projects)}/{target_count}")
            print(f"📥 Need to collect {target_count - len(self.existing_projects)}  new projects")
            
            # Use collector
            from collectors.collect_seattle_projects import SeattleProjectCollector
            collector = SeattleProjectCollector(token=self.token)
            
            # Calculate needed users
            needed = target_count - len(self.existing_projects)
            estimated_users = (needed // 10) + 100  # Average 10 projects per user
            
            # Collect new projects (skip existing)
            print(f"🔍 Searching for more Seattle developers...")
            users = collector.search_seattle_users(
                sort="followers",
                max_users=min(estimated_users, 1000)
            )
            
            new_projects = []
            with tqdm(total=needed, desc="Collecting new projects") as pbar:
                for user in users:
                    if len(new_projects) >= needed:
                        break
                    
                    repos = collector.get_user_repositories(user["login"])
                    
                    for repo in repos:
                        repo_name = repo["full_name"]
                        
                        # Skipped已存在的
                        if repo_name in self.existing_repos:
                            continue
                        
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
                            "owner": user,
                            "is_fork": repo["fork"],
                            "is_archived": repo.get("archived", False),
                            "last_stats_update": datetime.now().isoformat(),
                        }
                        
                        new_projects.append(project)
                        pbar.update(1)
                        
                        if len(new_projects) >= needed:
                            break
            
            # 添加新專案
            if new_projects:
                self.add_new_projects(
                    new_projects,
                    max_total=target_count,
                    replace_strategy="lowest_stars"
                )
        
        print(f"\n✅ 專案池Updating完成!")
        print(f"📊 Current projects: {len(self.existing_projects)}")
        print(f"⭐ Highest stars: {self.existing_projects[0]['stars']} ({self.existing_projects[0]['name_with_owner']})")
        print(f"⭐ Lowest stars: {self.existing_projects[-1]['stars']} ({self.existing_projects[-1]['name_with_owner']})")


def main():
    """Main function - 智能Updating示例"""
    collector = IncrementalProjectCollector(
        data_file="data/seattle_projects_10000.json"
    )
    
    # 智能Updating: Refresh 7  day old data + 補充到 10000 個
    collector.collect_with_smart_update(
        target_count=10000,
        refresh_days=7,
        collect_new=True
    )


if __name__ == "__main__":
    main()
