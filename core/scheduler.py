import os
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from parser.runner import run_parse_cycle
from parser.proxy import ProxyPool

logger = logging.getLogger(__name__)

proxy_pool = ProxyPool()


def start_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    interval = int(os.environ.get("PARSE_INTERVAL_MINUTES", 10))

    scheduler.add_job(
        run_parse_cycle, "interval",
        minutes=interval,
        kwargs={"bot": bot, "proxy_pool": proxy_pool},
        id="parse", max_instances=1, coalesce=True,
    )

    logger.info("Scheduler configured: interval=%dmin", interval)
    return scheduler
