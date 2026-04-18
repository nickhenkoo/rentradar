import logging
import os
import sys

import sentry_sdk
from dotenv import load_dotenv

load_dotenv()

from bot.app import build_application

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=os.environ.get("LOG_LEVEL", "INFO"),
    stream=sys.stdout,
)
# httpx logs full URLs (including bot token) — suppress to WARNING
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# ── Sentry ────────────────────────────────────────────────────────────────────
_sentry_dsn = os.environ.get("SENTRY_DSN", "")
if _sentry_dsn and not _sentry_dsn.startswith("https://xxxx"):
    sentry_sdk.init(
        dsn=_sentry_dsn,
        traces_sample_rate=0.1,
        environment=os.environ.get("ENVIRONMENT", "production"),
    )
    sentry_sdk.capture_message("RentRadar bot started", level="info")
    logging.info("Sentry enabled")

# ── Telegram log channel ──────────────────────────────────────────────────────
_log_channel = os.environ.get("LOG_CHANNEL_ID", "").strip()
_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if _log_channel and _bot_token:
    from core.tg_log_handler import TelegramLogHandler
    _tg_handler = TelegramLogHandler(token=_bot_token, channel_id=_log_channel)
    logging.getLogger().addHandler(_tg_handler)
    logging.info("Telegram log channel enabled: %s", _log_channel)
    # Startup notification — send directly so it always arrives regardless of log level
    import httpx as _httpx
    _httpx.post(
        f"https://api.telegram.org/bot{_bot_token}/sendMessage",
        json={"chat_id": _log_channel, "text": "🟢 <b>RentRadar bot started</b>", "parse_mode": "HTML"},
        timeout=5,
    )

if __name__ == "__main__":
    # run_polling manages the event loop itself; scheduler starts via post_init hook
    app = build_application()
    logging.info("Bot starting...")
    app.run_polling(drop_pending_updates=True)
