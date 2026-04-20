import logging
from datetime import datetime, timedelta

import sentry_sdk

import core.db as db
from core import notifier
from core.matcher import find_matching_filters
from core.models import User
from parser.sslv import SsLvParser
from parser.proxy import ProxyPool

logger = logging.getLogger(__name__)

_consecutive_empty_cycles = 0
# IDs of listings that existed in DB at bot startup — never alert on these
_preexisting_ids: set[str] | None = None


async def _load_preexisting_ids() -> None:
    global _preexisting_ids
    if _preexisting_ids is not None:
        return
    result = db.get_client().table("listings").select("id").execute()
    _preexisting_ids = {r["id"] for r in result.data}
    logger.info("Loaded %d preexisting listing IDs — will not alert on these", len(_preexisting_ids))


async def run_parse_cycle(bot, proxy_pool: ProxyPool = None) -> None:
    if proxy_pool is None:
        proxy_pool = ProxyPool()

    try:
        await _run_parse_cycle_inner(bot, proxy_pool)
    except Exception as e:
        logger.error("Unhandled exception in parse cycle: %s", e, exc_info=True)
        sentry_sdk.capture_exception(e)


async def _run_parse_cycle_inner(bot, proxy_pool: ProxyPool) -> None:
    global _consecutive_empty_cycles

    parser = SsLvParser(proxy_pool)
    listings = await parser.fetch_listings()

    if not listings:
        _consecutive_empty_cycles += 1
        logger.warning("Parse cycle returned 0 listings (consecutive: %d)", _consecutive_empty_cycles)
        if _consecutive_empty_cycles >= 3:
            msg = f"3+ consecutive empty parse cycles ({_consecutive_empty_cycles}) — check ss.lv selectors"
            logger.error(msg)
            sentry_sdk.capture_message(msg, level="error")
        return

    _consecutive_empty_cycles = 0
    logger.info("Fetched %d listings across all cities", len(listings))

    all_filters = await db.get_all_active_filters()
    if not all_filters:
        for listing in listings:
            await db.save_listing(listing)
        return

    all_users: dict[int, User] = {}

    await _load_preexisting_ids()

    now = datetime.utcnow()

    for listing in listings:
        is_new, created_at = await db.save_listing(listing)

        if listing.id in _preexisting_ids:
            continue

        # Skip listings older than 20 minutes to avoid flooding after downtime
        if not is_new and (now - created_at) > timedelta(minutes=20):
            continue

        matched = await find_matching_filters(listing, all_filters)
        if not matched:
            continue

        if listing.contacts:
            await db.update_listing_contacts(listing.id, listing.contacts)

        for f in matched:
            if f.user_id not in all_users:
                user = await db.get_user(f.user_id)
                if user is None:
                    continue
                all_users[f.user_id] = user
            user = all_users[f.user_id]

            if user.alerts_paused:
                continue

            already_sent = await db.has_alert_been_sent(user.id, listing.id)
            if already_sent:
                continue

            await notifier.send_alert(bot, user, listing, f)
            await db.mark_alert_sent(user.id, listing.id, filter_id=f.id)
