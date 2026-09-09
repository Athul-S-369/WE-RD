-- WE-RD PostgreSQL reference schema
-- Runtime schema is created by SQLAlchemy init_db() / weird-migrate.
-- This file is for operators and documentation.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sources (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  type VARCHAR(64) NOT NULL,
  url VARCHAR(1024) NOT NULL,
  credibility_score DOUBLE PRECISION DEFAULT 0.5,
  credibility_kind VARCHAR(64) DEFAULT 'community_post',
  active BOOLEAN DEFAULT TRUE,
  metadata JSONB DEFAULT '{}',
  last_fetched_at TIMESTAMPTZ,
  last_error TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS articles (
  id SERIAL PRIMARY KEY,
  source_id INTEGER REFERENCES sources(id),
  title VARCHAR(512) NOT NULL,
  url VARCHAR(2048) NOT NULL,
  canonical_url VARCHAR(2048) NOT NULL UNIQUE,
  author VARCHAR(255),
  published_at TIMESTAMPTZ,
  content TEXT DEFAULT '',
  summary TEXT DEFAULT '',
  content_hash VARCHAR(64),
  embedding JSONB,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stories (
  id SERIAL PRIMARY KEY,
  title VARCHAR(512) NOT NULL,
  slug VARCHAR(512) NOT NULL UNIQUE,
  dek TEXT DEFAULT '',
  description TEXT DEFAULT '',
  category VARCHAR(32),
  signal_score DOUBLE PRECISION DEFAULT 0,
  cracked_score INTEGER DEFAULT 0,
  rabbit_hole_score DOUBLE PRECISION DEFAULT 0,
  confidence VARCHAR(64) DEFAULT 'unverified',
  status VARCHAR(32) DEFAULT 'candidate',
  is_demo BOOLEAN DEFAULT FALSE,
  analysis JSONB DEFAULT '{}',
  security JSONB,
  leak JSONB,
  tags JSONB DEFAULT '[]',
  cluster_key VARCHAR(256),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS story_sources (
  id SERIAL PRIMARY KEY,
  story_id INTEGER NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
  article_id INTEGER REFERENCES articles(id),
  role VARCHAR(64) DEFAULT 'supporting',
  url VARCHAR(2048) NOT NULL,
  title VARCHAR(512) DEFAULT '',
  credibility_kind VARCHAR(64) DEFAULT 'secondary_reporting',
  credibility_score DOUBLE PRECISION DEFAULT 0.5
);

CREATE TABLE IF NOT EXISTS story_timeline (
  id SERIAL PRIMARY KEY,
  story_id INTEGER NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
  occurred_at TIMESTAMPTZ NOT NULL,
  headline VARCHAR(512) NOT NULL,
  body TEXT DEFAULT '',
  source_url VARCHAR(2048)
);

CREATE TABLE IF NOT EXISTS videos (
  id SERIAL PRIMARY KEY,
  story_id INTEGER NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
  video_id VARCHAR(64) NOT NULL,
  title VARCHAR(512) NOT NULL,
  channel VARCHAR(255) DEFAULT '',
  url VARCHAR(1024) NOT NULL,
  duration_seconds INTEGER,
  published_at TIMESTAMPTZ,
  description TEXT DEFAULT '',
  thumbnail VARCHAR(1024),
  relevance_score DOUBLE PRECISION DEFAULT 0,
  technical BOOLEAN DEFAULT TRUE,
  UNIQUE (story_id, video_id)
);

CREATE TABLE IF NOT EXISTS projects (
  id SERIAL PRIMARY KEY,
  story_id INTEGER NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  url VARCHAR(1024) NOT NULL,
  host VARCHAR(64) DEFAULT 'github',
  stars INTEGER,
  language VARCHAR(64),
  description TEXT DEFAULT '',
  metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS editions (
  id SERIAL PRIMARY KEY,
  issue_number INTEGER NOT NULL UNIQUE,
  week_start TIMESTAMPTZ NOT NULL UNIQUE,
  week_end TIMESTAMPTZ NOT NULL,
  status VARCHAR(32) DEFAULT 'draft',
  published_at TIMESTAMPTZ,
  masthead VARCHAR(255) DEFAULT 'The strange side of engineering.',
  week_in_numbers JSONB DEFAULT '{}',
  is_demo BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS edition_stories (
  id SERIAL PRIMARY KEY,
  edition_id INTEGER NOT NULL REFERENCES editions(id) ON DELETE CASCADE,
  story_id INTEGER NOT NULL REFERENCES stories(id),
  section VARCHAR(128) NOT NULL,
  sort_order INTEGER DEFAULT 0,
  featured BOOLEAN DEFAULT FALSE,
  UNIQUE (edition_id, story_id, section)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
  id SERIAL PRIMARY KEY,
  kind VARCHAR(32) NOT NULL,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  finished_at TIMESTAMPTZ,
  status VARCHAR(32) DEFAULT 'running',
  metrics JSONB DEFAULT '{}',
  error TEXT
);

CREATE TABLE IF NOT EXISTS llm_cache (
  id SERIAL PRIMARY KEY,
  cache_key VARCHAR(128) UNIQUE NOT NULL,
  provider VARCHAR(32) NOT NULL,
  prompt_name VARCHAR(128) NOT NULL,
  response JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
