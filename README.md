# RentRadar Latvia

Telegram bot that monitors ss.lv 24/7 and sends instant alerts when a new rental listing matches your filters.

**Bot:** [@ApartmentsLVBot](https://t.me/ApartmentsLVBot) · **Landing:** [rentradar.one](https://rentradar.one)

---

## What it does

- Scans ss.lv every 5–30 minutes across all Latvian cities
- Matches listings against user-defined filters (city, district, price, rooms, floor, series, long-term only)
- Sends Telegram alerts with photo, price, address, and floor
- Detects hot listings (≥10% below market median)
- Saves listings with personal notes
- Weekly market analytics digest
- Payments via Telegram Stars

**Languages:** English · Russian · Latvian

---

## Stack

| Layer | Tech |
|---|---|
| Bot | python-telegram-bot v20 |
| Database | Supabase (PostgreSQL) |
| Cache / dedup | Upstash Redis |
| Scraping | httpx + BeautifulSoup4 + lxml |
| Scheduler | APScheduler |
| Error tracking | Sentry |
| Hosting | Railway (worker + web) |

---

## Local setup

```bash
cp .env.example .env   # fill in all values
python3 -m pip install -r requirements.txt
python3 main.py        # bot worker
python3 web.py         # landing page on :8080
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | From @BotFather |
| `ADMIN_ID` | ✅ | Your Telegram user ID |
| `SUPABASE_URL` | ✅ | `https://xxxx.supabase.co` |
| `SUPABASE_KEY` | ✅ | Service role key |
| `UPSTASH_REDIS_REST_URL` | ✅ | |
| `UPSTASH_REDIS_REST_TOKEN` | ✅ | |
| `PROXY_API_KEY` | — | Webshare.io REST API key |
| `SENTRY_DSN` | — | Leave empty to disable |
| `LOG_CHANNEL_ID` | — | Telegram channel for WARNING+ logs |
| `PARSE_INTERVAL_PAID_MINUTES` | — | Default: 5 |
| `PARSE_INTERVAL_FREE_MINUTES` | — | Default: 30 |

---

## Database

Apply migrations in order using the Supabase SQL editor:

```
supabase/001_users.sql
supabase/002_filters.sql
supabase/003_listings.sql
supabase/004_sent_alerts.sql
supabase/005_price_history.sql
supabase/006_subscriptions.sql
supabase/007_filters_extra_fields.sql
supabase/008_listings_extra_fields.sql
supabase/009_users_pause_saved_listings.sql
supabase/010_saved_listings_note.sql
```

---

## Deploy (Railway)

1. Push repo to GitHub
2. Railway → New Project → Deploy from GitHub
3. Railway detects `Procfile` and creates two services:
   - `worker` — bot process (no public port)
   - `web` — landing page (assign `rentradar.one` domain)
4. Set all required env vars in Railway dashboard

```
worker: python3 main.py
web:    python3 web.py
```

Python version is pinned to **3.12** via `.python-version`.

---

## Pricing

| | Free | Pro (5 €/mo) |
|---|---|---|
| Search filters | Unlimited | Unlimited |
| Alert interval | 30 min | 5 min |
| Hot listing alerts | — | ✅ |
| Price history | — | ✅ |
| Weekly analytics | — | ✅ |
| Save listings + notes | ✅ | ✅ |
