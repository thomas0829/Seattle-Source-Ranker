"""
Celery worker for scoring repositories
Implements the SSR influence scoring model
"""
from typing import Dict, List, Optional
from celery_config import celery_app
from sqlmodel import Session, create_engine, select
from models import Repository, Score, PyPIStats, get_database_url
from datetime import datetime
import math


# Database setup
engine = create_engine(get_database_url(use_sqlite=True))


def normalize(value: float, max_value: float) -> float:
    """Normalize value to 0-1 range"""
    return value / max_value if max_value > 0 else 0


def log_normalize(value: float, max_value: float) -> float:
    """Logarithmic normalization for huge ranges (downloads)"""
    if value <= 0 or max_value <= 0:
        return 0
    return math.log10(value + 1) / math.log10(max_value + 1)


def age_weight(created_at: datetime) -> float:
    """Calculate age weight (older = more mature)"""
    years = (datetime.utcnow() - created_at).days / 365
    return years / (years + 2) if years > 0 else 0.3


def health_score(open_issues: int) -> float:
    """Calculate health score (fewer issues = better)"""
    return 1 - (open_issues / (open_issues + 10))


@celery_app.task(name="workers.score_worker.calculate_scores")
def calculate_scores(language: Optional[str] = None, force_recalculate: bool = False) -> Dict:
    """
    Calculate influence scores for repositories.
    
    SSR Scoring Formula:
    - GitHub Score (0-1): 0.4*stars + 0.25*forks + 0.15*watchers + 0.1*age + 0.1*health
    - Python: Final = 0.4*GitHub + 0.6*PyPI
    - C++: Final = 0.7*GitHub + 0.3*Releases
    - Others: Final = GitHub
    
    Args:
        language: Filter by language (None = all)
        force_recalculate: Recalculate even if scores exist
        
    Returns:
        Summary of scoring operation
    """
    
    with Session(engine) as session:
        # Get repositories
        query = select(Repository)
        if language:
            query = query.where(Repository.language == language)
        
        repos = session.exec(query).all()
        
        if not repos:
            return {"status": "no_repos", "count": 0}
        
        # Find max values for normalization
        max_stars = max(r.stars for r in repos)
        max_forks = max(r.forks for r in repos)
        max_watchers = max(r.watchers for r in repos)
        
        # For PyPI normalization
        pypi_repos = [r for r in repos if r.language == "Python" and r.pypi_stats]
        max_pypi_downloads = 0
        if pypi_repos:
            max_pypi_downloads = max(
                r.pypi_stats.downloads_last_month or 0
                for r in pypi_repos
            )
        
        scores_calculated = 0
        
        for repo in repos:
            # Check if score already exists
            if not force_recalculate:
                existing_score = session.exec(
                    select(Score)
                    .where(Score.repository_id == repo.id)
                    .order_by(Score.calculated_at.desc())
                ).first()
                
                if existing_score:
                    continue
            
            # Calculate GitHub score components
            S = normalize(repo.stars, max_stars)
            F = normalize(repo.forks, max_forks)
            W = normalize(repo.watchers, max_watchers)
            T = age_weight(repo.created_at)
            H = health_score(repo.open_issues)
            
            github_score = 0.4 * S + 0.25 * F + 0.15 * W + 0.10 * T + 0.10 * H
            
            # Calculate language-specific scores
            pypi_score = None
            npm_score = None
            release_score = None
            final_score = github_score
            
            # Python: Add PyPI downloads
            if repo.language == "Python" and repo.pypi_stats:
                downloads = repo.pypi_stats.downloads_last_month or 0
                pypi_score = log_normalize(downloads, max_pypi_downloads)
                final_score = 0.4 * github_score + 0.6 * pypi_score
            
            # C++: Add release downloads
            elif repo.language == "C++":
                if repo.release_count > 0:
                    release_score = normalize(repo.release_count, 100)
                    final_score = 0.7 * github_score + 0.3 * release_score
            
            # Create score record
            score = Score(
                repository_id=repo.id,
                github_score=github_score,
                pypi_score=pypi_score,
                npm_score=npm_score,
                release_score=release_score,
                final_score=final_score,
                scoring_version="1.0",
                calculated_at=datetime.utcnow(),
                components={
                    "stars_norm": S,
                    "forks_norm": F,
                    "watchers_norm": W,
                    "age_weight": T,
                    "health_score": H,
                    "max_stars": max_stars,
                    "max_forks": max_forks,
                    "max_watchers": max_watchers
                }
            )
            
            session.add(score)
            scores_calculated += 1
        
        session.commit()
        
        # Calculate rankings
        _calculate_rankings(session, language)
        
        return {
            "status": "completed",
            "language": language or "all",
            "repositories": len(repos),
            "scores_calculated": scores_calculated
        }


def _calculate_rankings(session: Session, language: Optional[str] = None):
    """Calculate rankings based on final scores"""
    
    # Global ranking
    query = (
        select(Score)
        .join(Repository)
        .order_by(Score.final_score.desc())
    )
    
    if language:
        query = query.where(Repository.language == language)
    
    scores = session.exec(query).all()
    
    for rank, score in enumerate(scores, 1):
        score.rank = rank
    
    # Language-specific ranking
    if not language:
        languages = session.exec(
            select(Repository.language).distinct()
        ).all()
        
        for lang in languages:
            if not lang:
                continue
            
            lang_scores = session.exec(
                select(Score)
                .join(Repository)
                .where(Repository.language == lang)
                .order_by(Score.final_score.desc())
            ).all()
            
            for rank, score in enumerate(lang_scores, 1):
                score.rank_by_language = rank
    
    session.commit()


@celery_app.task(name="workers.score_worker.calculate_all_languages")
def calculate_all_languages() -> Dict:
    """
    Calculate scores for all languages in parallel.
    """
    
    with Session(engine) as session:
        languages = session.exec(
            select(Repository.language).distinct()
        ).all()
    
    # Filter out None
    languages = [lang for lang in languages if lang]
    
    # Dispatch tasks
    task_ids = []
    for lang in languages:
        result = calculate_scores.delay(language=lang)
        task_ids.append(result.id)
    
    return {
        "status": "dispatched",
        "languages": languages,
        "task_count": len(task_ids),
        "task_ids": task_ids
    }


if __name__ == "__main__":
    print("🚀 Score worker ready")
    print("   Tasks: calculate_scores, calculate_all_languages")
