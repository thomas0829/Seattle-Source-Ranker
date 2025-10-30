"""
FastAPI REST API for Seattle-Source-Ranker
Provides endpoints for querying data and triggering tasks
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
from sqlmodel import Session, create_engine, select
from models import Repository, Owner, Score, FetchTask, get_database_url
from workers.fetch_worker import fetch_repositories, fetch_multi_language, verify_seattle_locations
from workers.score_worker import calculate_scores, calculate_all_languages
from datetime import datetime
import os


# Initialize FastAPI
app = FastAPI(
    title="Seattle-Source-Ranker API",
    description="Industrial-grade GitHub repository ranking system focused on Seattle area developers",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
engine = create_engine(get_database_url(use_sqlite=True))


# Pydantic models for API responses
class RepositoryResponse(BaseModel):
    id: int
    name_with_owner: str
    name: str
    description: Optional[str]
    url: str
    stars: int
    forks: int
    watchers: int
    language: Optional[str]
    owner_login: str
    owner_location: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScoreResponse(BaseModel):
    repository_id: int
    repository_name: str
    github_score: float
    pypi_score: Optional[float]
    final_score: float
    rank: Optional[int]
    rank_by_language: Optional[int]
    calculated_at: datetime


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class StatsResponse(BaseModel):
    total_repositories: int
    total_owners: int
    seattle_area_owners: int
    languages: dict
    top_languages: List[dict]


# Health check
@app.get("/")
async def root():
    return {
        "service": "Seattle-Source-Ranker API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        with Session(engine) as session:
            # Test database connection
            session.exec(select(Repository).limit(1)).first()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Repository endpoints
@app.get("/repositories", response_model=List[RepositoryResponse])
async def list_repositories(
    language: Optional[str] = None,
    min_stars: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=1000),
    offset: int = Query(default=0, ge=0),
    seattle_only: bool = False
):
    """
    List repositories with filters.
    
    - **language**: Filter by programming language
    - **min_stars**: Minimum star count
    - **limit**: Maximum results (max 1000)
    - **offset**: Pagination offset
    - **seattle_only**: Only show Seattle-area developers
    """
    
    with Session(engine) as session:
        query = select(Repository).join(Owner)
        
        if language:
            query = query.where(Repository.language == language)
        
        if min_stars > 0:
            query = query.where(Repository.stars >= min_stars)
        
        if seattle_only:
            query = query.where(Owner.is_seattle_area == True)
        
        query = query.order_by(Repository.stars.desc()).offset(offset).limit(limit)
        
        repos = session.exec(query).all()
        
        # Format response
        results = []
        for repo in repos:
            results.append(RepositoryResponse(
                id=repo.id,
                name_with_owner=repo.name_with_owner,
                name=repo.name,
                description=repo.description,
                url=repo.url,
                stars=repo.stars,
                forks=repo.forks,
                watchers=repo.watchers,
                language=repo.language,
                owner_login=repo.owner.login if repo.owner else "unknown",
                owner_location=repo.owner.location if repo.owner else None,
                created_at=repo.created_at
            ))
        
        return results


@app.get("/repositories/{repo_id}")
async def get_repository(repo_id: int):
    """Get detailed information for a specific repository"""
    
    with Session(engine) as session:
        repo = session.get(Repository, repo_id)
        
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Get latest score
        latest_score = session.exec(
            select(Score)
            .where(Score.repository_id == repo_id)
            .order_by(Score.calculated_at.desc())
        ).first()
        
        return {
            "repository": repo,
            "owner": repo.owner,
            "score": latest_score,
            "pypi_stats": repo.pypi_stats
        }


@app.get("/rankings", response_model=List[ScoreResponse])
async def get_rankings(
    language: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    seattle_only: bool = True
):
    """
    Get ranked repositories by influence score.
    
    - **language**: Filter by programming language
    - **limit**: Number of results
    - **seattle_only**: Only Seattle-area developers
    """
    
    with Session(engine) as session:
        query = (
            select(Score, Repository)
            .join(Repository)
            .join(Owner)
            .order_by(Score.final_score.desc())
        )
        
        if language:
            query = query.where(Repository.language == language)
        
        if seattle_only:
            query = query.where(Owner.is_seattle_area == True)
        
        query = query.limit(limit)
        
        results = session.exec(query).all()
        
        rankings = []
        for score, repo in results:
            rankings.append(ScoreResponse(
                repository_id=repo.id,
                repository_name=repo.name_with_owner,
                github_score=score.github_score,
                pypi_score=score.pypi_score,
                final_score=score.final_score,
                rank=score.rank,
                rank_by_language=score.rank_by_language,
                calculated_at=score.calculated_at
            ))
        
        return rankings


@app.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """Get overall statistics about the dataset"""
    
    with Session(engine) as session:
        total_repos = len(session.exec(select(Repository)).all())
        total_owners = len(session.exec(select(Owner)).all())
        seattle_owners = len(session.exec(
            select(Owner).where(Owner.is_seattle_area == True)
        ).all())
        
        # Language distribution
        lang_query = select(Repository.language).where(Repository.language != None)
        languages = session.exec(lang_query).all()
        
        lang_counts = {}
        for lang in languages:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
        
        # Top languages
        top_langs = sorted(
            [{"language": k, "count": v} for k, v in lang_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]
        
        return StatsResponse(
            total_repositories=total_repos,
            total_owners=total_owners,
            seattle_area_owners=seattle_owners,
            languages=lang_counts,
            top_languages=top_langs
        )


# Task management endpoints
@app.post("/tasks/fetch", response_model=TaskResponse)
async def trigger_fetch(
    location: str = "seattle",
    language: Optional[str] = None,
    min_stars: int = 100,
    max_results: int = 1000
):
    """
    Trigger a data fetch task.
    
    - **location**: Location to search
    - **language**: Programming language (None = all)
    - **min_stars**: Minimum stars
    - **max_results**: Maximum results
    """
    
    task_id = f"{location}_{language or 'all'}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    if language:
        query = f"location:{location} language:{language} stars:>={min_stars}"
    else:
        query = f"location:{location} stars:>={min_stars}"
    
    # Dispatch Celery task
    fetch_repositories.delay(
        task_id=task_id,
        search_query=query,
        max_results=max_results
    )
    
    return TaskResponse(
        task_id=task_id,
        status="dispatched",
        message=f"Fetch task started for {language or 'all languages'}"
    )


@app.post("/tasks/fetch-all-languages", response_model=TaskResponse)
async def trigger_fetch_all_languages(
    location: str = "seattle",
    min_stars: int = 100,
    max_results_per_lang: int = 1000
):
    """
    Trigger parallel fetch for all major programming languages.
    """
    
    result = fetch_multi_language.delay(
        location=location,
        min_stars=min_stars,
        max_results_per_lang=max_results_per_lang
    )
    
    return TaskResponse(
        task_id=result.id,
        status="dispatched",
        message=f"Multi-language fetch task started"
    )


@app.post("/tasks/calculate-scores", response_model=TaskResponse)
async def trigger_score_calculation(
    language: Optional[str] = None,
    force_recalculate: bool = False
):
    """
    Trigger score calculation task.
    
    - **language**: Calculate for specific language (None = all)
    - **force_recalculate**: Recalculate existing scores
    """
    
    if language:
        result = calculate_scores.delay(
            language=language,
            force_recalculate=force_recalculate
        )
    else:
        result = calculate_all_languages.delay()
    
    return TaskResponse(
        task_id=result.id,
        status="dispatched",
        message=f"Score calculation started for {language or 'all languages'}"
    )


@app.post("/tasks/verify-locations", response_model=TaskResponse)
async def trigger_location_verification():
    """Verify which owners are in Seattle area"""
    
    result = verify_seattle_locations.delay()
    
    return TaskResponse(
        task_id=result.id,
        status="dispatched",
        message="Location verification task started"
    )


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    
    with Session(engine) as session:
        task = session.exec(
            select(FetchTask).where(FetchTask.task_id == task_id)
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status,
            "progress": task.progress,
            "total": task.total,
            "items_collected": task.items_collected,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "errors": task.errors
        }


@app.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = Query(default=50, le=500)
):
    """List recent tasks"""
    
    with Session(engine) as session:
        query = select(FetchTask).order_by(FetchTask.created_at.desc())
        
        if status:
            query = query.where(FetchTask.status == status)
        
        query = query.limit(limit)
        
        tasks = session.exec(query).all()
        
        return [
            {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": task.status,
                "items_collected": task.items_collected,
                "created_at": task.created_at,
                "completed_at": task.completed_at
            }
            for task in tasks
        ]


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
