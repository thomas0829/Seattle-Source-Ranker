"""
Cursor Manager for checkpoint-based data collection
Supports fault tolerance and resume capability
"""
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime


class CursorManager:
    """
    Manages GraphQL cursors for checkpoint recovery.
    Allows long-running data collection to resume after interruption.
    """
    
    def __init__(self, checkpoint_dir: str = "data/checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    def save_checkpoint(
        self,
        task_id: str,
        cursor: str,
        progress: Dict[str, Any]
    ) -> None:
        """
        Save a checkpoint for a data collection task.
        
        Args:
            task_id: Unique identifier for the task (e.g., "seattle_python_repos")
            cursor: Current GraphQL cursor position
            progress: Additional progress info (count, timestamp, etc.)
        """
        checkpoint_file = os.path.join(self.checkpoint_dir, f"{task_id}.json")
        
        checkpoint_data = {
            "task_id": task_id,
            "cursor": cursor,
            "progress": progress,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2)
        
        print(f"💾 Checkpoint saved: {task_id} ({progress.get('count', 0)} items)")
    
    def load_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a checkpoint for a task.
        
        Args:
            task_id: Unique identifier for the task
            
        Returns:
            Checkpoint data or None if not found
        """
        checkpoint_file = os.path.join(self.checkpoint_dir, f"{task_id}.json")
        
        if not os.path.exists(checkpoint_file):
            return None
        
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            
            print(f"📦 Checkpoint loaded: {task_id}")
            print(f"   Resume from: {checkpoint['progress'].get('count', 0)} items")
            print(f"   Last updated: {checkpoint.get('timestamp', 'unknown')}")
            
            return checkpoint
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Failed to load checkpoint: {e}")
            return None
    
    def clear_checkpoint(self, task_id: str) -> bool:
        """
        Clear a checkpoint after successful completion.
        
        Args:
            task_id: Unique identifier for the task
            
        Returns:
            True if cleared successfully
        """
        checkpoint_file = os.path.join(self.checkpoint_dir, f"{task_id}.json")
        
        if os.path.exists(checkpoint_file):
            try:
                os.remove(checkpoint_file)
                print(f"✅ Checkpoint cleared: {task_id}")
                return True
            except OSError as e:
                print(f"⚠️  Failed to clear checkpoint: {e}")
                return False
        
        return False
    
    def list_checkpoints(self) -> list[str]:
        """
        List all available checkpoints.
        
        Returns:
            List of task IDs with checkpoints
        """
        if not os.path.exists(self.checkpoint_dir):
            return []
        
        checkpoints = []
        for filename in os.listdir(self.checkpoint_dir):
            if filename.endswith(".json"):
                task_id = filename[:-5]  # Remove .json
                checkpoints.append(task_id)
        
        return checkpoints
    
    def get_checkpoint_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get summary information about a checkpoint without full load.
        """
        checkpoint = self.load_checkpoint(task_id)
        if not checkpoint:
            return None
        
        return {
            "task_id": checkpoint["task_id"],
            "count": checkpoint["progress"].get("count", 0),
            "timestamp": checkpoint.get("timestamp"),
            "cursor": checkpoint.get("cursor", "")[:50] + "..."  # Truncate for display
        }


class IncrementalCollector:
    """
    Manages incremental data collection with automatic checkpoint recovery.
    Combines GraphQL client with cursor management.
    """
    
    def __init__(self, graphql_client, checkpoint_interval: int = 1000):
        """
        Args:
            graphql_client: Instance of GitHubGraphQLClient
            checkpoint_interval: Save checkpoint every N items
        """
        self.client = graphql_client
        self.cursor_manager = CursorManager()
        self.checkpoint_interval = checkpoint_interval
    
    def collect_with_resume(
        self,
        task_id: str,
        search_query: str,
        max_results: Optional[int] = None,
        force_restart: bool = False
    ) -> list[Dict]:
        """
        Collect data with automatic checkpoint and resume capability.
        
        Args:
            task_id: Unique identifier for this collection task
            search_query: GitHub search query
            max_results: Maximum number of results
            force_restart: Ignore existing checkpoint and start fresh
            
        Returns:
            List of collected repositories
        """
        all_repos = []
        start_cursor = None
        start_count = 0
        
        # Try to resume from checkpoint
        if not force_restart:
            checkpoint = self.cursor_manager.load_checkpoint(task_id)
            if checkpoint:
                start_cursor = checkpoint.get("cursor")
                start_count = checkpoint["progress"].get("count", 0)
                print(f"🔄 Resuming from checkpoint: {start_count} items already collected")
        
        # Define checkpoint callback
        def checkpoint_callback(cursor: str, count: int):
            total_count = start_count + count
            if total_count % self.checkpoint_interval == 0:
                self.cursor_manager.save_checkpoint(
                    task_id=task_id,
                    cursor=cursor,
                    progress={
                        "count": total_count,
                        "query": search_query
                    }
                )
        
        # Fetch repositories
        print(f"🚀 Starting collection: {task_id}")
        repos = self.client.fetch_all_repositories(
            query=search_query,
            max_results=max_results - start_count if max_results else None,
            checkpoint_callback=checkpoint_callback,
            progress_bar=True
        )
        
        all_repos.extend(repos)
        
        # Clear checkpoint on success
        if repos:
            self.cursor_manager.clear_checkpoint(task_id)
            print(f"✅ Collection complete: {len(repos)} new items (total: {start_count + len(repos)})")
        
        return all_repos


def main():
    """Demo usage of cursor management"""
    from graphql_client import GitHubGraphQLClient
    
    # Setup
    client = GitHubGraphQLClient()
    collector = IncrementalCollector(client, checkpoint_interval=500)
    
    # Collect with resume capability
    repos = collector.collect_with_resume(
        task_id="seattle_popular_repos",
        search_query="location:seattle stars:>100",
        max_results=2000
    )
    
    print(f"\n✅ Collected {len(repos)} repositories with checkpoint support")
    
    # List active checkpoints
    manager = CursorManager()
    checkpoints = manager.list_checkpoints()
    if checkpoints:
        print(f"\n📋 Active checkpoints: {', '.join(checkpoints)}")


if __name__ == "__main__":
    main()
