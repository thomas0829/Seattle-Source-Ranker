"""
Database models for Seattle-Source-Ranker
Using SQLModel for type-safe ORM with Pydantic validation
"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from sqlalchemy import Index


class Owner(SQLModel, table=True):
    """
    Repository owner (User or Organization)
    """
    __tablename__ = "owners"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    login: str = Field(index=True, unique=True)
    name: Optional[str] = None
    location: Optional[str] = Field(default=None, index=True)
    company: Optional[str] = None
    bio: Optional[str] = None
    owner_type: str = Field(default="User")  # User or Organization
    
    # Location verification
    is_seattle_area: bool = Field(default=False, index=True)
    location_verified_at: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    repositories: List["Repository"] = Relationship(back_populates="owner")
    
    class Config:
        json_schema_extra = {
            "example": {
                "login": "octocat",
                "name": "The Octocat",
                "location": "Seattle, WA",
                "company": "GitHub",
                "is_seattle_area": True
            }
        }


class Repository(SQLModel, table=True):
    """
    GitHub Repository with metrics and metadata
    """
    __tablename__ = "repositories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name_with_owner: str = Field(index=True, unique=True)
    name: str
    description: Optional[str] = None
    url: str
    
    # GitHub metrics
    stars: int = Field(default=0, index=True)
    forks: int = Field(default=0)
    watchers: int = Field(default=0)
    open_issues: int = Field(default=0)
    
    # Metadata
    language: Optional[str] = Field(default=None, index=True)
    languages: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    topics: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    license: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[datetime] = None
    
    # Release info
    release_count: int = Field(default=0)
    latest_release: Optional[str] = None
    
    # Owner relationship
    owner_id: Optional[int] = Field(default=None, foreign_key="owners.id")
    owner: Optional[Owner] = Relationship(back_populates="repositories")
    
    # Data collection metadata
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    data_source: str = Field(default="graphql")  # graphql or rest
    
    # Relationships
    scores: List["Score"] = Relationship(back_populates="repository")
    pypi_stats: Optional["PyPIStats"] = Relationship(back_populates="repository")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name_with_owner": "microsoft/vscode",
                "name": "vscode",
                "stars": 150000,
                "language": "TypeScript",
                "is_seattle_area": True
            }
        }


class Score(SQLModel, table=True):
    """
    Influence scores for repositories
    Supports multiple scoring versions and historical tracking
    """
    __tablename__ = "scores"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    repository_id: int = Field(foreign_key="repositories.id", index=True)
    
    # Score components (normalized 0-1)
    github_score: float = Field(default=0.0)
    pypi_score: Optional[float] = None
    npm_score: Optional[float] = None
    release_score: Optional[float] = None
    
    # Final composite score
    final_score: float = Field(default=0.0, index=True)
    
    # Ranking
    rank: Optional[int] = Field(default=None, index=True)
    rank_by_language: Optional[int] = None
    
    # Scoring metadata
    scoring_version: str = Field(default="1.0")
    calculated_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Raw component values for transparency
    components: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # Relationship
    repository: Optional[Repository] = Relationship(back_populates="scores")
    
    class Config:
        json_schema_extra = {
            "example": {
                "github_score": 0.85,
                "pypi_score": 0.92,
                "final_score": 0.89,
                "rank": 1
            }
        }


class PyPIStats(SQLModel, table=True):
    """
    PyPI download statistics for Python projects
    """
    __tablename__ = "pypi_stats"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    repository_id: int = Field(foreign_key="repositories.id", unique=True, index=True)
    
    package_name: str = Field(index=True)
    
    # Download stats
    downloads_last_day: Optional[int] = None
    downloads_last_week: Optional[int] = None
    downloads_last_month: Optional[int] = None
    
    # Package metadata
    latest_version: Optional[str] = None
    package_url: Optional[str] = None
    
    # Timestamps
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship
    repository: Optional[Repository] = Relationship(back_populates="pypi_stats")
    
    class Config:
        json_schema_extra = {
            "example": {
                "package_name": "numpy",
                "downloads_last_month": 50000000
            }
        }


class FetchTask(SQLModel, table=True):
    """
    Tracks data collection tasks for monitoring and debugging
    """
    __tablename__ = "fetch_tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(unique=True, index=True)
    task_type: str = Field(index=True)  # github_search, pypi_fetch, score_calculation
    
    # Task parameters
    query: Optional[str] = None
    parameters: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    # Status
    status: str = Field(default="pending", index=True)  # pending, running, completed, failed
    progress: int = Field(default=0)
    total: Optional[int] = None
    
    # Results
    items_collected: int = Field(default=0)
    errors: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Worker info
    worker_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "seattle_python_repos_20250101",
                "task_type": "github_search",
                "status": "completed",
                "items_collected": 5000
            }
        }


# Indexes for performance
Index("idx_repo_stars_lang", Repository.stars, Repository.language)
Index("idx_score_final_calc", Score.final_score, Score.calculated_at)
Index("idx_owner_location_verified", Owner.is_seattle_area, Owner.location)


def create_db_and_tables(engine):
    """
    Create all tables in the database
    """
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables created successfully")


def get_database_url(use_sqlite: bool = True) -> str:
    """
    Get database connection URL
    """
    if use_sqlite:
        return "sqlite:///data/ssr.db"
    else:
        # PostgreSQL for production
        import os
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "ssr")
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASSWORD", "password")
        return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"


if __name__ == "__main__":
    """Initialize database"""
    from sqlmodel import create_engine
    import os
    
    os.makedirs("data", exist_ok=True)
    
    # Use SQLite for development
    database_url = get_database_url(use_sqlite=True)
    engine = create_engine(database_url, echo=True)
    
    print(f"📦 Creating database: {database_url}")
    create_db_and_tables(engine)
    print("✅ Database initialized successfully!")
