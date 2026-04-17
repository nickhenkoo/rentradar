-- Migration 005: price_history table
CREATE TABLE IF NOT EXISTS price_history (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id  TEXT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    price       INTEGER NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_price_history_listing ON price_history(listing_id, recorded_at DESC);
