-- Migration 009: global alert pause + saved listings
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS alerts_paused BOOLEAN DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS saved_listings (
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    listing_id  TEXT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    saved_at    TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, listing_id)
);
