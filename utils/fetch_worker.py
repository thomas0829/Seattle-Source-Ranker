"""
Celery workers for distributed GitHub data fetching
"""
from typing import Dict, List, Optional
from celery import Task
from celery_config import celery_app
from graphql_client import GitHubGraphQLClient
from cursor_manager import CursorManager
from sqlmodel import Session, create_engine, select
from models import Repository, Owner, FetchTask, get_database_url
from datetime import datetime
import os


# Database setup
engine = create_engine(get_database_url(use_sqlite=True))


class DatabaseTask(Task):
    """Base task with database session management"""
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = Session(engine)
        return self._db


@celery_app.task(bind=True, base=DatabaseTask, name="workers.fetch_worker.fetch_repositories")
def fetch_repositories(
    self,
    task_id: str,
    search_query: str,
    max_results: Optional[int] = None
) -> Dict:
    """
    Fetch repositories using GraphQL with cursor pagination.
    Distributed worker task with checkpoint recovery.
    
    Args:
        task_id: Unique task identifier
        search_query: GitHub search query
        max_results: Maximum results to fetch
        
    Returns:
        Task result summary
    """
    
    # Create or update fetch task record
    with Session(engine) as session:
        fetch_task = session.exec(
            select(FetchTask).where(FetchTask.task_id == task_id)
        ).first()
        
        if not fetch_task:
            fetch_task = FetchTask(
                task_id=task_id,
                task_type="github_search",
                query=search_query,
                parameters={"max_results": max_results},
                status="running",
                started_at=datetime.utcnow(),
                worker_id=self.request.id
            )
            session.add(fetch_task)
        else:
            fetch_task.status = "running"
            fetch_task.started_at = datetime.utcnow()
            fetch_task.worker_id = self.request.id
        
        session.commit()
    
    try:
        # Initialize GraphQL client
        client = GitHubGraphQLClient()
        cursor_manager = CursorManager()
        
        # Check for existing checkpoint
        checkpoint = cursor_manager.load_checkpoint(task_id)
        start_cursor = checkpoint.get("cursor") if checkpoint else None
        
        # Progress callback
        def checkpoint_callback(cursor: str, count: int):
            cursor_manager.save_checkpoint(
                task_id=task_id,
                cursor=cursor,
                progress={
                    "count": count,
                    "query": search_query
                }
            )
            
            # Update task progress
            with Session(engine) as session:
                task = session.exec(
                    select(FetchTask).where(FetchTask.task_id == task_id)
                ).first()
                if task:
                    task.progress = count
                    session.commit()
        
        # Fetch repositories
        print(f"🚀 Worker {self.request.id}: Fetching repositories for '{search_query}'")
        repos = client.fetch_all_repositories(
            query=search_query,
            max_results=max_results,
            checkpoint_callback=checkpoint_callback,
            progress_bar=False  # Disable in worker
        )
        
        # Save to database
        saved_count = 0
        with Session(engine) as session:
            for repo_data in repos:
                # Get or create owner
                owner_login = repo_data["owner"]["login"]
                owner = session.exec(
                    select(Owner).where(Owner.login == owner_login)
                ).first()
                
                if not owner:
                    owner = Owner(
                        login=owner_login,
                        name=repo_data["owner"].get("name"),
                        location=repo_data["owner"].get("location"),
                        company=repo_data["owner"].get("company"),
                    )
                    session.add(owner)
                    session.commit()
                    session.refresh(owner)
                
                # Check if repo already exists
                existing = session.exec(
                    select(Repository).where(
                        Repository.name_with_owner == repo_data["name_with_owner"]
                    )
                ).first()
                
                if existing:
                    # Update existing
                    existing.stars = repo_data["stars"]
                    existing.forks = repo_data["forks"]
                    existing.watchers = repo_data["watchers"]
                    existing.open_issues = repo_data["open_issues"]
                    existing.updated_at = datetime.fromisoformat(
                        repo_data["updated_at"].replace("Z", "+00:00")
                    )
                    existing.fetched_at = datetime.utcnow()
                else:
                    # Create new
                    repo = Repository(
                        name_with_owner=repo_data["name_with_owner"],
                        name=repo_data["name"],
                        description=repo_data.get("description"),
                        url=repo_data["url"],
                        stars=repo_data["stars"],
                        forks=repo_data["forks"],
                        watchers=repo_data["watchers"],
                        open_issues=repo_data["open_issues"],
                        language=repo_data.get("language"),
                        languages=repo_data.get("languages"),
                        topics=repo_data.get("topics"),
                        license=repo_data.get("license"),
                        created_at=datetime.fromisoformat(
                            repo_data["created_at"].replace("Z", "+00:00")
                        ),
                        updated_at=datetime.fromisoformat(
                            repo_data["updated_at"].replace("Z", "+00:00")
                        ),
                        pushed_at=datetime.fromisoformat(
                            repo_data["pushed_at"].replace("Z", "+00:00")
                        ) if repo_data.get("pushed_at") else None,
                        release_count=repo_data.get("release_count", 0),
                        latest_release=repo_data.get("latest_release"),
                        owner_id=owner.id,
                        data_source="graphql"
                    )
                    session.add(repo)
                    saved_count += 1
            
            session.commit()
        
        # Update task as completed
        with Session(engine) as session:
            task = session.exec(
                select(FetchTask).where(FetchTask.task_id == task_id)
            ).first()
            if task:
                task.status = "completed"
                task.completed_at = datetime.utcnow()
                task.items_collected = len(repos)
                task.progress = len(repos)
                session.commit()
        
        # Clear checkpoint
        cursor_manager.clear_checkpoint(task_id)
        
        result = {
            "task_id": task_id,
            "status": "success",
            "repos_fetched": len(repos),
            "repos_saved": saved_count,
            "query": search_query
        }
        
        print(f"✅ Worker {self.request.id}: Completed - {len(repos)} repos fetched")
        return result
        
    except Exception as e:
        # Update task as failed
        with Session(engine) as session:
            task = session.exec(
                select(FetchTask).where(FetchTask.task_id == task_id)
            ).first()
            if task:
                task.status = "failed"
                task.completed_at = datetime.utcnow()
                task.errors = [str(e)]
                session.commit()
        
        print(f"❌ Worker {self.request.id}: Failed - {str(e)}")
        raise


@celery_app.task(name="workers.fetch_worker.fetch_multi_language")
def fetch_multi_language(
    location: str = "seattle",
    min_stars: int = 100,
    max_results_per_lang: int = 1000
) -> Dict:
    """
    Fetch repositories for multiple languages in parallel.
    Dispatches sub-tasks for each language.
    
    Args:
        location: Location query
        min_stars: Minimum stars threshold
        max_results_per_lang: Max results per language
        
    Returns:
        Summary of all sub-tasks
    """
    
    languages = [
        "Python", "JavaScript", "TypeScript", "Go", "Rust",
        "Java", "C++", "C#", "Ruby", "PHP",
        "Swift", "Kotlin", "Dart", "Scala", "Haskell"
    ]
    
    task_ids = []
    for lang in languages:
        task_id = f"{location}_{lang.lower()}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        query = f"location:{location} language:{lang} stars:>={min_stars}"
        
        # Dispatch async task
        fetch_repositories.delay(
            task_id=task_id,
            search_query=query,
            max_results=max_results_per_lang
        )
        
        task_ids.append(task_id)
    
    return {
        "status": "dispatched",
        "languages": languages,
        "task_ids": task_ids,
        "total_tasks": len(task_ids)
    }


@celery_app.task(name="workers.fetch_worker.verify_seattle_locations")
def verify_seattle_locations() -> Dict:
    """
    Verify which owners are actually in Seattle area.
    Updates Owner.is_seattle_area field.
    """
    
    seattle_keywords = [
        "seattle", "redmond", "bellevue", "kirkland",
        "tacoma", "everett", "renton", "sammamish",
        "washington", "wa", "puget sound"
    ]
    
    verified_count = 0
    
    with Session(engine) as session:
        owners = session.exec(select(Owner)).all()
        
        for owner in owners:
            if owner.location:
                location_lower = owner.location.lower()
                is_seattle = any(
                    keyword in location_lower
                    for keyword in seattle_keywords
                )
                
                if is_seattle != owner.is_seattle_area:
                    owner.is_seattle_area = is_seattle
                    owner.location_verified_at = datetime.utcnow()
                    verified_count += 1
        
        session.commit()
    
    return {
        "status": "completed",
        "verified_count": verified_count
    }


if __name__ == "__main__":
    print("🚀 Starting Celery worker...")
    print("   Queues: fetch, score, pypi")
    print("   Tasks: fetch_repositories, fetch_multi_language, verify_seattle_locations")
