-- DEFCON scoring v2 — schema additions
-- Run against existing databases. Idempotent.

ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS defcon_trigger TEXT;

ALTER TABLE last_refresh
    ADD COLUMN IF NOT EXISTS min_level_until_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS min_level_floor    SMALLINT;
