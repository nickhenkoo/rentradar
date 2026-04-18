import logging
from datetime import datetime, timedelta
from collections import defaultdict

import core.db as db
from bot.i18n import t
from core.models import city_name

logger = logging.getLogger(__name__)


async def send_weekly_analytics(bot) -> None:
    """Send weekly market digest to all users with analytics feature."""
    users = await db.get_users_with_feature("analytics")
    if not users:
        return

    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

    # Fetch last week's listings — use created_at, exclude only confirmed short-term
    supabase = db.get_client()
    result = (
        supabase.table("listings")
        .select("city, price, rooms, district")
        .gt("first_seen", week_ago)
        .neq("is_long_term", False)
        .execute()
    )
    listings = result.data

    for user in users:
        try:
            text = _build_analytics(user, listings)
            await bot.send_message(
                chat_id=user.id,
                text=text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error("Failed to send analytics to user %d: %s", user.id, e)


def _build_analytics(user, listings: list[dict]) -> str:
    lang = user.language
    lines = [t("analytics_header", lang)]

    by_city: dict[str, list[int]] = defaultdict(list)
    for l in listings:
        if l.get("price") and l.get("city"):
            by_city[l["city"]].append(l["price"])

    if not by_city:
        lines.append(t("analytics_no_data", lang))
        return "\n".join(lines)

    for city_key, prices in sorted(by_city.items(), key=lambda x: -len(x[1])):
        avg = int(sum(prices) / len(prices))
        cname = city_name(city_key, lang)
        lines.append(f"🏙 <b>{cname}</b>: {len(prices)} listings, avg {avg} €/mo")

    return "\n".join(lines)
