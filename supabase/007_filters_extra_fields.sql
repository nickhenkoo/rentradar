-- Migration 007: extra filter fields
ALTER TABLE filters
    ADD COLUMN IF NOT EXISTS area_max        INTEGER,
    ADD COLUMN IF NOT EXISTS floor_min       INTEGER,
    ADD COLUMN IF NOT EXISTS floor_max       INTEGER,
    ADD COLUMN IF NOT EXISTS series          TEXT,
    ADD COLUMN IF NOT EXISTS long_term_only  BOOLEAN DEFAULT TRUE;
