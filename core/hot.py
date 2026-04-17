import os
import logging
from core.models import Listing

logger = logging.getLogger(__name__)


async def is_hot(listing: Listing, redis) -> bool:
    """
    Returns True if:
    1. Listing has at least one photo
    2. Price is >= HOT_THRESHOLD_PCT% below median for city+rooms bucket
    """
    if not listing.image_urls:
        return False
    if not listing.price:
        return False

    median_key = f"median:{listing.city}:{listing.rooms or 'any'}"
    try:
        median = await redis.get(median_key)
    except Exception:
        return False

    if not median:
        return False

    threshold = float(os.environ.get("HOT_LISTING_THRESHOLD_PCT", 10)) / 100
    return listing.price <= float(median) * (1 - threshold)


async def update_medians(listings: list[Listing], redis) -> None:
    """Update rolling median prices in Redis after each parse cycle."""
    from collections import defaultdict
    buckets: dict[str, list[int]] = defaultdict(list)

    for listing in listings:
        if listing.price and listing.is_long_term is not False:
            key = f"median:{listing.city}:{listing.rooms or 'any'}"
            buckets[key].append(listing.price)

    for key, prices in buckets.items():
        if prices:
            prices.sort()
            median = prices[len(prices) // 2]
            try:
                await redis.set(key, str(median), ex=60 * 60 * 24 * 30)  # 30 days TTL
            except Exception as e:
                logger.debug("Failed to update median %s: %s", key, e)
