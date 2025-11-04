-- Initialize Seattle Source Ranker Database

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Owners table (GitHub users)
CREATE TABLE IF NOT EXISTS owners (
    id SERIAL PRIMARY KEY,
    login VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    location VARCHAR(255),
    company VARCHAR(255),
    email VARCHAR(255),
    bio TEXT,
    avatar_url TEXT,
    html_url TEXT,
    seattle_verified BOOLEAN DEFAULT FALSE,
    verification_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Repositories table
CREATE TABLE IF NOT EXISTS repositories (
    id SERIAL PRIMARY KEY,
    github_id BIGINT UNIQUE,
    name_with_owner VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    homepage TEXT,
    stars INTEGER DEFAULT 0,
    forks INTEGER DEFAULT 0,
    watchers INTEGER DEFAULT 0,
    open_issues INTEGER DEFAULT 0,
    language VARCHAR(100),
    topics TEXT[],
    license VARCHAR(100),
    is_archived BOOLEAN DEFAULT FALSE,
    is_fork BOOLEAN DEFAULT FALSE,
    has_issues BOOLEAN DEFAULT TRUE,
    has_wiki BOOLEAN DEFAULT TRUE,
    owner_id INTEGER REFERENCES owners(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    pushed_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scores table
CREATE TABLE IF NOT EXISTS scores (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    github_score DECIMAL(10, 6) NOT NULL,
    pypi_score DECIMAL(10, 6),
    npm_score DECIMAL(10, 6),
    final_score DECIMAL(10, 6) NOT NULL,
    rank INTEGER,
    rank_by_language INTEGER,
    age_weight DECIMAL(5, 4),
    health_score DECIMAL(5, 4),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_id, calculated_at)
);

-- Collection tasks table (for tracking distributed collection)
CREATE TABLE IF NOT EXISTS collection_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    total_items INTEGER,
    completed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    worker_id VARCHAR(100),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_repositories_owner_id ON repositories(owner_id);
CREATE INDEX IF NOT EXISTS idx_repositories_language ON repositories(language);
CREATE INDEX IF NOT EXISTS idx_repositories_stars ON repositories(stars DESC);
CREATE INDEX IF NOT EXISTS idx_repositories_created_at ON repositories(created_at);
CREATE INDEX IF NOT EXISTS idx_scores_repository_id ON scores(repository_id);
CREATE INDEX IF NOT EXISTS idx_scores_final_score ON scores(final_score DESC);
CREATE INDEX IF NOT EXISTS idx_scores_rank ON scores(rank);
CREATE INDEX IF NOT EXISTS idx_owners_location ON owners(location);
CREATE INDEX IF NOT EXISTS idx_owners_seattle_verified ON owners(seattle_verified);
CREATE INDEX IF NOT EXISTS idx_collection_tasks_status ON collection_tasks(status);

-- Views for common queries
CREATE OR REPLACE VIEW top_repositories AS
SELECT 
    r.name_with_owner,
    r.description,
    r.language,
    r.stars,
    r.forks,
    r.url,
    o.login as owner_login,
    o.location as owner_location,
    s.final_score,
    s.rank,
    s.rank_by_language
FROM repositories r
JOIN owners o ON r.owner_id = o.id
LEFT JOIN scores s ON r.id = s.repository_id
WHERE o.seattle_verified = TRUE
ORDER BY s.final_score DESC NULLS LAST;

CREATE OR REPLACE VIEW top_by_language AS
SELECT 
    r.language,
    r.name_with_owner,
    r.stars,
    s.final_score,
    s.rank_by_language,
    o.location
FROM repositories r
JOIN owners o ON r.owner_id = o.id
LEFT JOIN scores s ON r.id = s.repository_id
WHERE o.seattle_verified = TRUE AND r.language IS NOT NULL
ORDER BY r.language, s.rank_by_language NULLS LAST;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER update_owners_updated_at BEFORE UPDATE ON owners
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repositories_updated_at BEFORE UPDATE ON repositories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ssr_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ssr_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ssr_user;
