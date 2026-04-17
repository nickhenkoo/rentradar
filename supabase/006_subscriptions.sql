-- Migration 006: subscriptions table (Telegram Stars payments)
CREATE TABLE IF NOT EXISTS subscriptions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature      TEXT NOT NULL,    -- 'speed' | 'hot' | 'history' | 'analytics' | 'pro'
    expires_at   TIMESTAMPTZ NOT NULL,
    purchased_at TIMESTAMPTZ DEFAULT NOW(),
    stars_paid   INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id, expires_at DESC);
