-- Migration 010: personal notes on saved listings
ALTER TABLE saved_listings
    ADD COLUMN IF NOT EXISTS note TEXT;
