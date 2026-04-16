-- Cybersecurity Defcon Dashboard — Database Schema
-- PostgreSQL 16

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Core articles table
CREATE TABLE articles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guid            TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    summary         TEXT,
    url             TEXT NOT NULL,
    source          TEXT NOT NULL CHECK (source IN ('bleeping_computer', 'dark_reading', 'help_net_security', 'security_week', 'the_hacker_news')),
    published_at    TIMESTAMPTZ NOT NULL,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_categories  TEXT[],
    defcon_score    NUMERIC(5,2) NOT NULL DEFAULT 0,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_articles_published_at ON articles (published_at DESC) WHERE is_deleted = FALSE;
CREATE INDEX idx_articles_source ON articles (source) WHERE is_deleted = FALSE;
CREATE INDEX idx_articles_fetched_at ON articles (fetched_at DESC) WHERE is_deleted = FALSE;

-- Read state per browser session (no auth required)
CREATE TABLE article_read_state (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id  UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    session_id  TEXT NOT NULL,
    is_read     BOOLEAN NOT NULL DEFAULT TRUE,
    read_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (article_id, session_id)
);

CREATE INDEX idx_read_state_session ON article_read_state (session_id);
CREATE INDEX idx_read_state_article ON article_read_state (article_id);

-- Defcon score history (for sparkline trend)
CREATE TABLE defcon_history (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    score                NUMERIC(5,2) NOT NULL,
    level                SMALLINT NOT NULL CHECK (level BETWEEN 1 AND 5),
    computed_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    article_window       INTEGER NOT NULL,
    contributing_factors JSONB
);

CREATE INDEX idx_defcon_history_computed_at ON defcon_history (computed_at DESC);

-- Deduplication audit log
CREATE TABLE dedup_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint     TEXT NOT NULL UNIQUE,
    canonical_id    UUID REFERENCES articles(id) ON DELETE SET NULL,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    first_seen_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dedup_log_fingerprint ON dedup_log (fingerprint);

-- Last refresh timestamp (single row)
CREATE TABLE last_refresh (
    id              INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    refreshed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO last_refresh (id, refreshed_at) VALUES (1, NOW());
