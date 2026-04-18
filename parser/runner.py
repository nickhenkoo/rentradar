import os
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
_startup_time = datetime.utcnow()


def _get_redis():
    """Lazy-init Upstash Redis client."""
    from upstash_redis import Redis
    return Redis(
        url=os.environ["UPSTASH_REDIS_REST_URL"],
        token=os.environ["UPSTASH_REDIS_REST_TOKEN"],
    )


async def run_parse_cycle(bot, tier: str = "free", proxy_pool: ProxyPool = None) -> None:
    """
    Full parse cycle.
    tier: 'paid' — notify paid users only; 'free' — notify all users.
    """
    if proxy_pool is None:
        proxy_pool = ProxyPool()

    try:
        await _run_parse_cycle_inner(bot, tier, proxy_pool)
    except Exception as e:
        logger.error("Unhandled exception in parse cycle: %s", e, exc_info=True)
        sentry_sdk.capture_exception(e)


async def _run_parse_cycle_inner(bot, tier: str, proxy_pool: ProxyPool) -> None:
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

    redis = _get_redis()

    # Update median prices for hot detection
    from core.hot import update_medians, is_hot
    await update_medians(listings, redis)

    all_filters = await db.get_all_active_filters()
    if not all_filters:
        for listing in listings:
            await db.save_listing(listing)
        return

    all_users: dict[int, User] = {}

    free_interval = int(os.environ.get("PARSE_INTERVAL_FREE_MINUTES", 30))
    max_age = timedelta(minutes=free_interval * 2)
    now = datetime.utcnow()

    # Grace period: skip alerts for the first full free cycle after startup
    # so the DB can populate without flooding users with pre-existing listings.
    grace_period = timedelta(minutes=free_interval + 5)
    in_grace = (now - _startup_time) < grace_period

    for listing in listings:
        is_new, created_at = await db.save_listing(listing)

        if in_grace:
            continue

        # paid cycle: skip listings already seen (processed by a previous paid cycle)
        # free cycle: always proceed — paid cycle may have saved the listing first,
        #             so is_new=False even though free users were never notified.
        #             But skip listings older than 2× free_interval to avoid flooding.
        if tier == "paid" and not is_new:
            continue
        if tier == "free" and not is_new and (now - created_at) > max_age:
            continue

        matched = await find_matching_filters(listing, all_filters)
        if not matched:
            continue

        # contact_url is already in listing.contacts from the index page.
        # Image is already extracted from index page in .800.jpg quality.
        if listing.contacts:
            await db.update_listing_contacts(listing.id, listing.contacts)

        hot = await is_hot(listing, redis)

        for f in matched:
            if f.user_id not in all_users:
                user = await db.get_user(f.user_id)
                if user is None:
                    continue
                all_users[f.user_id] = user
            user = all_users[f.user_id]

            # Tier filtering: 'paid' job notifies only paid-speed users
            if tier == "paid" and not user.has("speed"):
                continue

            # Global pause check
            if user.alerts_paused:
                continue

            already_sent = await db.has_alert_been_sent(user.id, listing.id)
            if already_sent:
                continue

            await notifier.send_alert(bot, user, listing, f, is_hot=(hot and user.has("hot")))
            await db.mark_alert_sent(user.id, listing.id, filter_id=f.id)


def _extract_price_from_detail(html: str) -> int | None:
    """
    Extract rental price from an ss.lv listing detail page.
    Tries multiple selectors in priority order, then falls back to regex scan.
    Returns None if no reliable price found.
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")

    # Try known ss.lv price table cell patterns (detail page)
    for sel in ("#tdo_8", "td.ads_price", ".ads_price", "#price_field"):
        el = soup.select_one(sel)
        if el:
            m = re.search(r'(\d[\d\s]{1,6})\s*€', el.get_text())
            if m:
                return int(m.group(1).replace(" ", ""))

    # Fallback: scan all text nodes for "NNN €/month" pattern
    # Use strict pattern to avoid matching e.g. "40 €/day"
    for text in soup.stripped_strings:
        m = re.search(r'(\d[\d\s]{1,5})\s*€\s*/?\s*(m[eē]n|month|mēn)', text, re.IGNORECASE)
        if m:
            return int(m.group(1).replace(" ", ""))

    return None


async def recheck_prices(proxy_pool: ProxyPool = None) -> None:
    """
    Re-check known listing URLs and record price changes.
    Only fetches listings seen in the last 30 days.
    """
    db_client = db.get_client()
    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
    result = (
        db_client.table("listings")
        .select("id, url, price")
        .gt("last_seen", cutoff)
        .execute()
    )
    if not result.data:
        return

    if proxy_pool is None:
        proxy_pool = ProxyPool()

    import httpx, re, asyncio, random
    from bs4 import BeautifulSoup

    for row in result.data[:50]:  # cap at 50 per cycle to avoid hammering
        await asyncio.sleep(random.uniform(3.0, 7.0))
        try:
            html = await fetch_listing_price(row["url"], proxy_pool)
            if html is None:
                continue
            new_price = _extract_price_from_detail(html)
            if new_price is None:
                continue
            if new_price != row.get("price") and 10 <= new_price <= 50000:
                await db.save_price_point(row["id"], new_price)
                db_client.table("listings").update({"price": new_price}).eq("id", row["id"]).execute()
                logger.info("Price change detected for %s: %s → %s", row["id"], row.get("price"), new_price)
        except Exception as e:
            logger.debug("Price recheck failed for %s: %s", row["id"], e)


async def fetch_listing_price(url: str, pool: ProxyPool):
    from parser.proxy import fetch_with_proxy
    return await fetch_with_proxy(url, pool, retries=2)
