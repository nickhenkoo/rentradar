-- Migration 004: sent_alerts table
-- Tracks which listings were already sent to each user (dedup key)
CREATE TABLE IF NOT EXISTS sent_alerts (
    user_id     BIGINT NOT NULL,
    listing_id  TEXT NOT NULL,
    filter_id   UUID,
    sent_at     TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, listing_id)
);
