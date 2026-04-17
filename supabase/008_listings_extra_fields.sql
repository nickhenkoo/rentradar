-- Migration 008: extra listing fields
ALTER TABLE listings
    ADD COLUMN IF NOT EXISTS floor        INTEGER,
    ADD COLUMN IF NOT EXISTS floor_total  INTEGER,
    ADD COLUMN IF NOT EXISTS series       TEXT,
    ADD COLUMN IF NOT EXISTS is_long_term BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS contacts     JSONB,
    ADD COLUMN IF NOT EXISTS image_urls   TEXT[],
    ADD COLUMN IF NOT EXISTS description  TEXT,
    ADD COLUMN IF NOT EXISTS last_seen    TIMESTAMPTZ DEFAULT NOW();
