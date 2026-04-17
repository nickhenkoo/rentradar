import os
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from parser.runner import run_parse_cycle, recheck_prices
from core.analytics import send_weekly_analytics
from parser.proxy import ProxyPool

logger = logging.getLogger(__name__)

proxy_pool = ProxyPool()


def start_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    paid_interval = int(os.environ.get("PARSE_INTERVAL_PAID_MINUTES", 5))
    free_interval = int(os.environ.get("PARSE_INTERVAL_FREE_MINUTES", 30))
    recheck_hours = int(os.environ.get("PRICE_RECHECK_INTERVAL_HOURS", 6))

    # Fast job — notifies paid users first
    scheduler.add_job(
        run_parse_cycle, "interval",
        minutes=paid_interval,
        kwargs={"bot": bot, "tier": "paid", "proxy_pool": proxy_pool},
        id="parse_paid", max_instances=1, coalesce=True,
    )

    # Slow job — notifies all free users
    scheduler.add_job(
        run_parse_cycle, "interval",
        minutes=free_interval,
        kwargs={"bot": bot, "tier": "free", "proxy_pool": proxy_pool},
        id="parse_free", max_instances=1, coalesce=True,
    )

    # Price recheck
    scheduler.add_job(
        recheck_prices, "interval",
        hours=recheck_hours,
        kwargs={"proxy_pool": proxy_pool},
        id="price_recheck", max_instances=1, coalesce=True,
    )

    analytics_day = os.environ.get("ANALYTICS_DAY", "monday").lower()[:3]  # "monday" → "mon"
    analytics_hour = int(os.environ.get("ANALYTICS_HOUR", 9))

    scheduler.add_job(
        send_weekly_analytics, "cron",
        day_of_week=analytics_day, hour=analytics_hour,
        kwargs={"bot": bot},
        id="analytics", max_instances=1,
    )

    logger.info(
        "Scheduler configured: paid=%dmin free=%dmin recheck=%dh",
        paid_interval, free_interval, recheck_hours,
    )
    return scheduler
