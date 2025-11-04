"""
Distributed Collection Coordinator

Coordinates multiple Celery workers to collect Seattle projects in parallel.
Uses Redis as message broker and PostgreSQL for data persistence.

Usage:
    python3 distributed_collector.py --target 10000 --workers 5 --batch-size 10
"""
import argparse
import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from celery import group
from celery.result import GroupResult

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.collection_worker import (
    search_seattle_users_task,
    fetch_users_batch_task,
    collect_seattle_projects_task
)
from utils.celery_config import celery_app


class DistributedCollector:
    """
    Coordinator for distributed data collection
    
    Responsibilities:
    - Search for Seattle developers (REST API)
    - Split developers into batches
    - Distribute batches to workers
    - Monitor progress
    - Aggregate and save results
    """
    
    def __init__(self, batch_size: int = 10):
        """
        Args:
            batch_size: Number of users per worker batch
        """
        self.batch_size = batch_size
        self.results = []
    
    def search_users(self, max_users: int) -> List[str]:
        """
        Search for Seattle developers using REST API
        
        Args:
            max_users: Maximum number of users to find
            
        Returns:
            List of GitHub usernames
        """
        import requests
        
        print(f"🔍 Step 1: Searching for Seattle developers...")
        print(f"   Target: {max_users} users")
        
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        usernames = []
        page = 1
        per_page = 100
        
        while len(usernames) < max_users:
            url = f"https://api.github.com/search/users"
            params = {
                "q": "location:seattle",
                "per_page": per_page,
                "page": page,
                "sort": "repositories",
                "order": "desc"
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"   ⚠️ Warning: API returned status {response.status_code}")
                break
            
            data = response.json()
            users = data.get("items", [])
            
            if not users:
                break
            
            for user in users:
                usernames.append(user["login"])
                if len(usernames) >= max_users:
                    break
            
            page += 1
        
        print(f"✅ Found {len(usernames)} developers")
        return usernames
    
    def create_batches(self, usernames: List[str]) -> List[List[str]]:
        """
        Split users into batches for parallel processing
        
        Args:
            usernames: List of GitHub usernames
            
        Returns:
            List of username batches
        """
        batches = [
            usernames[i:i + self.batch_size]
            for i in range(0, len(usernames), self.batch_size)
        ]
        
        print(f"\n📦 Step 2: Created {len(batches)} batches")
        print(f"   Batch size: {self.batch_size} users/batch")
        print(f"   Total users: {len(usernames)}")
        
        return batches
    
    def distribute_tasks(self, batches: List[List[str]]) -> GroupResult:
        """
        Distribute batches to workers using Celery group
        
        Args:
            batches: List of username batches
            
        Returns:
            Celery GroupResult for monitoring
        """
        print(f"\n⚡ Step 3: Distributing tasks to workers...")
        print(f"   Spawning {len(batches)} parallel tasks")
        
        # Create parallel tasks
        job = group(fetch_users_batch_task.s(batch) for batch in batches)
        result = job.apply_async()
        
        print(f"✅ Tasks submitted to queue")
        return result
    
    def monitor_progress(self, result: GroupResult, total_batches: int):
        """
        Monitor and display progress of distributed tasks
        
        Args:
            result: Celery GroupResult
            total_batches: Total number of batches
        """
        print(f"\n📊 Step 4: Monitoring progress...")
        print(f"   Total batches: {total_batches}")
        print(f"   Waiting for workers...\n")
        
        start_time = time.time()
        last_completed = 0
        shown_errors = set()
        
        while not result.ready():
            completed = result.completed_count()
            
            # Check for failures
            failed_count = 0
            for task_result in result.results:
                if task_result.failed():
                    failed_count += 1
                    task_id = task_result.id
                    if task_id not in shown_errors:
                        try:
                            error = task_result.result
                            print(f"   ❌ Task {task_id[:8]} failed: {error}", flush=True)
                        except Exception as e:
                            print(f"   ❌ Task {task_id[:8]} failed: {str(e)}", flush=True)
                        shown_errors.add(task_id)
            
            if completed != last_completed or failed_count > 0:
                elapsed = time.time() - start_time
                progress = (completed / total_batches) * 100
                
                status = f"   Progress: {completed}/{total_batches} batches ({progress:.1f}%)"
                if failed_count > 0:
                    status += f" | Failed: {failed_count}"
                status += f" | Elapsed: {elapsed:.1f}s"
                
                print(status, flush=True)
                last_completed = completed
            
            time.sleep(2)
        
        elapsed = time.time() - start_time
        print(f"\n✅ All tasks completed in {elapsed:.1f}s", flush=True)
    
    def aggregate_results(self, result: GroupResult, target_projects: int) -> Dict[str, Any]:
        """
        Aggregate results from all workers
        
        Args:
            result: Celery GroupResult
            target_projects: Target number of projects
            
        Returns:
            Aggregated results
        """
        print(f"\n📥 Step 5: Aggregating results...")
        
        batch_results = result.get(timeout=1800)  # 30 minutes timeout
        
        all_projects = []
        total_users_successful = 0
        total_users_failed = 0
        
        for batch_result in batch_results:
            all_projects.extend(batch_result["repos"])
            total_users_successful += batch_result["successful_users"]
            total_users_failed += batch_result["failed_users"]
        
        print(f"   Raw projects collected: {len(all_projects)}")
        print(f"   Successful users: {total_users_successful}")
        print(f"   Failed users: {total_users_failed}")
        
        # Sort by stars and limit
        all_projects.sort(key=lambda x: x["stars"], reverse=True)
        top_projects = all_projects[:target_projects]
        
        total_stars = sum(p["stars"] for p in top_projects)
        
        print(f"\n   Top {len(top_projects)} projects selected")
        print(f"   Total stars: {total_stars:,}")
        
        if top_projects:
            top_project = top_projects[0]
            print(f"   #1 project: {top_project['name_with_owner']} ({top_project['stars']:,} stars)")
        
        return {
            "total_projects": len(top_projects),
            "total_stars": total_stars,
            "successful_users": total_users_successful,
            "failed_users": total_users_failed,
            "projects": top_projects,
            "collected_at": datetime.utcnow().isoformat()
        }
    
    def save_results(self, results: Dict[str, Any], output_file: str):
        """
        Save aggregated results to JSON file
        
        Args:
            results: Aggregated results
            output_file: Output file path
        """
        print(f"\n💾 Step 6: Saving results...")
        
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved to: {output_file}")
    
    def collect(
        self,
        target_projects: int = 10000,
        max_users: int = 1000,
        output_file: str = None
    ) -> Dict[str, Any]:
        """
        Main collection workflow
        
        Args:
            target_projects: Target number of projects
            max_users: Maximum users to search
            output_file: Output file path (optional)
            
        Returns:
            Collection results
        """
        print(f"🚀 Starting Distributed Collection")
        print(f"=" * 60)
        print(f"Target Projects: {target_projects}")
        print(f"Max Users: {max_users}")
        print(f"Batch Size: {self.batch_size}")
        print(f"=" * 60)
        
        start_time = time.time()
        
        try:
            # Step 1: Search users
            usernames = self.search_users(max_users)
            
            if not usernames:
                raise ValueError("No users found")
            
            # Step 2: Create batches
            batches = self.create_batches(usernames)
            
            # Step 3: Distribute tasks
            result = self.distribute_tasks(batches)
            
            # Step 4: Monitor progress
            self.monitor_progress(result, len(batches))
            
            # Step 5: Aggregate results
            aggregated = self.aggregate_results(result, target_projects)
            
            # Step 6: Save results
            if output_file:
                self.save_results(aggregated, output_file)
            
            # Summary
            elapsed = time.time() - start_time
            print(f"\n" + "=" * 60)
            print(f"✅ Collection Complete!")
            print(f"=" * 60)
            print(f"Total Time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
            print(f"Projects: {aggregated['total_projects']}")
            print(f"Stars: {aggregated['total_stars']:,}")
            print(f"Users: {aggregated['successful_users']} successful, "
                  f"{aggregated['failed_users']} failed")
            print(f"=" * 60)
            
            return aggregated
            
        except Exception as e:
            print(f"\n❌ Error during collection: {e}")
            raise


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Distributed Seattle project collector using Celery workers"
    )
    parser.add_argument(
        "--target",
        type=int,
        default=10000,
        help="Target number of projects to collect (default: 10000)"
    )
    parser.add_argument(
        "--max-users",
        type=int,
        default=1000,
        help="Maximum number of users to search (default: 1000)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of users per worker batch (default: 10)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file path (default: data/seattle_projects_distributed_<timestamp>.json)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Recommended number of Celery workers to start (default: 3)"
    )
    
    args = parser.parse_args()
    
    # Default output file
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"data/seattle_projects_distributed_{timestamp}.json"
    
    # Check environment
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    # Print worker recommendation
    print(f"\n💡 Make sure {args.workers} Celery workers are running!")
    print(f"   Use: python3 -m celery -A workers.collection_worker worker --loglevel=info --concurrency=2 -n workerN@%h")
    print(f"\n🚀 Starting collection now...\n")
    
    # Run collection
    collector = DistributedCollector(batch_size=args.batch_size)
    
    try:
        results = collector.collect(
            target_projects=args.target,
            max_users=args.max_users,
            output_file=args.output
        )
        
        print(f"\n✅ Success! Results saved to: {args.output}")
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Collection interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
