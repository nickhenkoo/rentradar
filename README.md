# RentRadar Latvia

Telegram bot that monitors ss.lv 24/7 and sends instant alerts when a new rental listing matches your filters.

**Bot:** [@ApartmentsLVBot](https://t.me/ApartmentsLVBot) · **Website:** [rentradar.one](https://rentradar.one)

---

## How it works

1. **Set your filters** — city, district, price range, rooms, floor, building series, long-term only
2. **We scan ss.lv** — every 10 minutes, around the clock, across all Latvian cities
3. **You get notified instantly** — Telegram message with photo, price, address, and a direct link

No account needed. Completely free. Works entirely inside Telegram.

---

## What's in the bot

### User commands

| Command | Description |
|---|---|
| `/start` | Language picker + onboarding |
| `/addfilter` | Create a search filter (guided flow) |
| `/myfilters` | View, pause, resume, or delete filters |
| `/saved` | Saved listings with personal notes |
| `/pause_all` / `/resume_all` | Stop and restart all alerts globally |
| `/language` | Switch language (EN / RU / LV) |
| `/help` | Show help |

### Filter options

Each filter supports:
- **City** — Riga, Jūrmala, Liepāja, Daugavpils, Jelgava, Rēzekne, Valmiera, Ventspils, Ogre
- **District** — all Riga districts (Centrs, Purvciems, Teika, etc.)
- **Price range** — min / max €/month
- **Rooms** — min / max
- **Area** — min / max m²
- **Floor** — min / max
- **Building series** — 103, 104, 119, 467, 602, Hrušč, Staļinka, Jaun., Private house
- **Long-term only** — skip daily/weekly rentals

Multiple filters can run simultaneously.

### Alert format

Each alert includes:
- Photo (if available on ss.lv)
- City + district + street address
- Price, rooms, area, floor, building series
- Which filter matched and its full criteria
- **[View]** button linking to ss.lv in the user's language
- **[Save]** button — adds to `/saved`
- **[Report]** button — flag irrelevant listings

### Saved listings

- Accessible via `/saved`
- Add a personal note to any saved listing via the 📝 button
- Notes are stored per user, per listing

### Promoted listings (B2B)

Agencies can pay to push a specific listing to all users with matching filters. The alert is labeled **⭐ Promoted listing** and bypasses the standard 10-minute cycle. Managed via `/admin_promote`.

---

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Bot framework | python-telegram-bot v20 |
| Database | Supabase (PostgreSQL) |
| HTTP | httpx (async) |
| Parsing | BeautifulSoup4 + lxml |
| Scheduler | APScheduler |
| Error tracking | Sentry + Telegram log channel |
| Deployment | Railway (worker + web dyno) |

---

## Running locally

```bash
git clone https://github.com/nickhenko/rentradar
cd rentradar
python3 -m pip install -r requirements.txt
cp .env.example .env   # fill in your secrets
python3 main.py
```

### Required environment variables

```
TELEGRAM_BOT_TOKEN
ADMIN_ID                  # your Telegram user ID
SUPABASE_URL
SUPABASE_KEY              # service role key
```

### Optional

```
UPSTASH_REDIS_REST_URL    # not required (hot detection removed)
UPSTASH_REDIS_REST_TOKEN
SENTRY_DSN
PROXY_API_KEY             # Webshare.io REST API key
PROXY_LIST_URL            # fallback proxy download URL
LOG_CHANNEL_ID            # Telegram channel for WARNING+ logs
PARSE_INTERVAL_MINUTES=10 # default: 10
```

---

## Admin commands

Visible only to `ADMIN_ID`. Access via the bot.

| Command | Description |
|---|---|
| `/admin` | Overview: users, listings, parser status |
| `/admin_promote <id_or_url>` | Push promoted alert to all matching users |
| `/admin_stats` | Analytics: top cities, avg budget, paused users |
| `/admin_broadcast <msg>` | Send message to all users |
| `/admin_user <id>` | View user info, filters |
| `/admin_grant <id> [months]` | Grant Pro bundle |
| `/admin_setplan <id> <plan>` | Change user plan |
| `/admin_test_alerts` | Send 5 test alerts to yourself |
| `/admin_refresh` | Clear your sent_alerts (for re-testing) |

### Promoted alert usage

```
/admin_promote sslv_12345678
/admin_promote https://www.ss.lv/lv/real-estate/flats/riga/centre/12345678.html
```

Looks up the listing in DB, finds all users with a matching active filter, sends each one a `⭐ Promoted listing` alert. Reports back: how many users reached and how many skipped (paused).

---

## Project structure

```
rentradar/
├── main.py                  # Entry point
├── requirements.txt
├── Procfile                 # Railway: worker + web
├── .env
│
├── bot/
│   ├── app.py               # Application builder, handler registration
│   ├── i18n.py              # All user-facing strings (EN/RU/LV)
│   ├── keyboards.py         # InlineKeyboardMarkup factories
│   └── handlers/
│       ├── start.py         # /start, /help
│       ├── language.py      # /language
│       ├── filters.py       # /addfilter — ConversationHandler
│       ├── listings.py      # /myfilters, /saved, /pause_all, /resume_all, notes
│       ├── feedback.py      # Rating prompts, listing reports
│       ├── subscription.py  # Stars payment handlers (kept, not registered — bot is free)
│       ├── premium.py       # Price history handler (kept, not registered)
│       └── admin.py         # Admin-only commands
│
├── parser/
│   ├── base.py              # Abstract BaseParser
│   ├── sslv.py              # ss.lv scraper — all Latvian cities
│   ├── proxy.py             # Webshare.io proxy pool with rotation
│   └── runner.py            # Parse cycle: fetch → dedup → match → alert
│
├── core/
│   ├── models.py            # Dataclasses, CITIES, SERIES, DISTRICTS
│   ├── db.py                # All Supabase CRUD
│   ├── matcher.py           # Match Listing against Filter
│   ├── notifier.py          # Format and send alerts
│   ├── hot.py               # Hot listing detection (unused — kept for reference)
│   ├── analytics.py         # Weekly digest (unused — kept for reference)
│   ├── scheduler.py         # APScheduler: single parse job every 10 min
│   └── tg_log_handler.py    # WARNING+ logs → Telegram channel
│
├── landing/
│   └── index.html           # SEO landing page (EN/RU/LV)
├── web.py                   # Flask server for landing page
└── supabase/                # SQL migrations 001–010
```

---

## Deployment (Railway)

Two services from the same repo:

```
worker: python3 main.py   # Telegram bot
web:    python3 web.py    # Landing page
```

Assign `rentradar.one` to the web service. All env vars are shared between both services.

After deploy: send `/start` to the bot, then `/admin` to verify parser status.
