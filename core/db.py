import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from supabase import create_client, Client
from postgrest.exceptions import APIError
from core.models import User, Filter, Listing, PricePoint, PRO_FEATURES

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


async def _retry(fn, retries: int = 3, delay: float = 2.0):
    """Retry a synchronous Supabase call on transient 5xx errors."""
    for attempt in range(retries):
        try:
            return fn()
        except APIError as e:
            code = str(e.args[0].get("code", "")) if e.args else ""
            if code in ("502", "503", "504") and attempt < retries - 1:
                logger.warning("Supabase transient error %s, retry %d/%d", code, attempt + 1, retries - 1)
                await asyncio.sleep(delay * (attempt + 1))
                continue
            raise
    raise RuntimeError("Unreachable")


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    return _client


def _parse_dt(raw) -> Optional[datetime]:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.replace(tzinfo=None)
    if isinstance(raw, str):
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    return None


def _row_to_user(row: dict, active_features: set) -> User:
    return User(
        id=row["id"],
        username=row.get("username"),
        first_name=row.get("first_name"),
        language=row.get("language", "en"),
        alerts_paused=row.get("alerts_paused", False),
        _active_features=active_features,
    )


def _row_to_filter(row: dict) -> Filter:
    return Filter(
        id=row["id"],
        user_id=row["user_id"],
        city=row["city"],
        label=row.get("label"),
        district=row.get("district"),
        price_min=row.get("price_min"),
        price_max=row.get("price_max"),
        rooms_min=row.get("rooms_min"),
        rooms_max=row.get("rooms_max"),
        area_min=row.get("area_min"),
        area_max=row.get("area_max"),
        floor_min=row.get("floor_min"),
        floor_max=row.get("floor_max"),
        series=row.get("series"),
        long_term_only=row.get("long_term_only", True),
        is_active=row.get("is_active", True),
    )


async def _get_active_features(user_id: int) -> set:
    db = get_client()
    now = datetime.utcnow().isoformat()
    result = (
        db.table("subscriptions")
        .select("feature")
        .eq("user_id", user_id)
        .gt("expires_at", now)
        .execute()
    )
    features = {r["feature"] for r in result.data}
    # If user has "pro", expand to all individual features
    if "pro" in features:
        features |= PRO_FEATURES
    return features


async def get_or_create_user(telegram_user) -> tuple:
    db = get_client()
    result = db.table("users").select("*").eq("id", telegram_user.id).execute()
    if result.data:
        features = await _get_active_features(telegram_user.id)
        return _row_to_user(result.data[0], features), False

    row = {
        "id": telegram_user.id,
        "username": telegram_user.username,
        "first_name": telegram_user.first_name,
        "language": "en",
    }
    result = db.table("users").insert(row).execute()
    return _row_to_user(result.data[0], set()), True


async def update_user_language(user_id: int, lang: str) -> None:
    get_client().table("users").update({"language": lang}).eq("id", user_id).execute()


async def get_user(user_id: int) -> Optional[User]:
    db = get_client()
    result = db.table("users").select("*").eq("id", user_id).execute()
    if not result.data:
        return None
    features = await _get_active_features(user_id)
    return _row_to_user(result.data[0], features)


async def get_user_filters(user_id: int) -> list[Filter]:
    result = (
        get_client().table("filters")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )
    return [_row_to_filter(r) for r in result.data]


async def count_active_filters(user_id: int) -> int:
    result = (
        get_client().table("filters")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )
    return result.count or 0


async def create_filter(user_id: int, **kwargs) -> Filter:
    result = get_client().table("filters").insert({"user_id": user_id, **kwargs}).execute()
    return _row_to_filter(result.data[0])


async def delete_filter(filter_id: str, user_id: int) -> None:
    get_client().table("filters").delete().eq("id", filter_id).eq("user_id", user_id).execute()


async def set_filter_active(filter_id: str, user_id: int, active: bool) -> None:
    get_client().table("filters").update({"is_active": active}).eq("id", filter_id).eq("user_id", user_id).execute()


async def save_listing(listing: Listing) -> tuple[bool, datetime]:
    """Returns (is_new, created_at). Updates last_seen if already known."""
    db = get_client()
    now = datetime.utcnow()
    result = await _retry(lambda: db.table("listings").select("id, created_at").eq("id", listing.id).execute())
    if result.data:
        await _retry(lambda: db.table("listings").update({"last_seen": now.isoformat()}).eq("id", listing.id).execute())
        created_at = _parse_dt(result.data[0].get("created_at")) or now
        return False, created_at

    row = {
        "id": listing.id,
        "source": listing.source,
        "url": listing.url,
        "city": listing.city,
        "title": listing.title,
        "district": listing.district,
        "street": listing.street,
        "price": listing.price,
        "rooms": listing.rooms,
        "area": listing.area,
        "floor": listing.floor,
        "floor_total": listing.floor_total,
        "series": listing.series,
        "is_long_term": listing.is_long_term,
        "contacts": listing.contacts or None,
        "image_urls": listing.image_urls or None,
        "description": listing.description,
    }
    try:
        inserted = await _retry(lambda: db.table("listings").insert(row).execute())
        created_at = _parse_dt(inserted.data[0].get("created_at")) if inserted.data else now
        # Record initial price point so price history starts from day one
        if listing.price:
            await save_price_point(listing.id, listing.price)
        return True, created_at or now
    except APIError as e:
        code = str(e.args[0].get("code", "")) if e.args else ""
        if code not in ("23505",):  # 23505 = unique_violation (duplicate), expected
            logger.warning("Unexpected DB error inserting listing %s: %s", listing.id, e)
        return False, now
    except Exception as e:
        logger.debug("Listing already exists: %s (%s)", listing.id, e)
        return False, now


async def update_listing_contacts(listing_id: str, contacts: dict) -> None:
    get_client().table("listings").update({"contacts": contacts}).eq("id", listing_id).execute()


async def get_all_active_filters() -> list[Filter]:
    result = get_client().table("filters").select("*").eq("is_active", True).execute()
    return [_row_to_filter(r) for r in result.data]


async def has_alert_been_sent(user_id: int, listing_id: str) -> bool:
    result = (
        get_client().table("sent_alerts")
        .select("user_id")
        .eq("user_id", user_id)
        .eq("listing_id", listing_id)
        .execute()
    )
    return bool(result.data)


async def mark_alert_sent(user_id: int, listing_id: str, filter_id: Optional[str] = None) -> None:
    try:
        row = {"user_id": user_id, "listing_id": listing_id}
        if filter_id:
            row["filter_id"] = filter_id
        get_client().table("sent_alerts").insert(row).execute()
    except Exception:
        pass


async def activate_feature(user_id: int, feature: str, months: int, stars_paid: int) -> None:
    db = get_client()
    now = datetime.utcnow()
    # Check if feature already active — extend if so
    existing = (
        db.table("subscriptions")
        .select("id, expires_at")
        .eq("user_id", user_id)
        .eq("feature", feature)
        .gt("expires_at", now.isoformat())
        .execute()
    )
    if existing.data:
        old_expires = _parse_dt(existing.data[0]["expires_at"])
        new_expires = (old_expires or now) + timedelta(days=30 * months)
        db.table("subscriptions").update({
            "expires_at": new_expires.isoformat(),
            "stars_paid": stars_paid,
        }).eq("id", existing.data[0]["id"]).execute()
    else:
        db.table("subscriptions").insert({
            "user_id": user_id,
            "feature": feature,
            "expires_at": (now + timedelta(days=30 * months)).isoformat(),
            "purchased_at": now.isoformat(),
            "stars_paid": stars_paid,
        }).execute()


async def get_user_subscriptions(user_id: int) -> list[dict]:
    now = datetime.utcnow().isoformat()
    result = (
        get_client().table("subscriptions")
        .select("feature, expires_at")
        .eq("user_id", user_id)
        .gt("expires_at", now)
        .execute()
    )
    return result.data


async def save_price_point(listing_id: str, price: int) -> None:
    try:
        get_client().table("price_history").insert({
            "listing_id": listing_id,
            "price": price,
            "recorded_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        logger.debug("Failed to save price point: %s", e)


async def get_price_history(listing_id: str) -> list[PricePoint]:
    from core.models import PricePoint
    result = (
        get_client().table("price_history")
        .select("*")
        .eq("listing_id", listing_id)
        .order("recorded_at", desc=True)
        .limit(30)
        .execute()
    )
    return [
        PricePoint(
            listing_id=r["listing_id"],
            price=r["price"],
            recorded_at=_parse_dt(r["recorded_at"]) or datetime.utcnow(),
        )
        for r in result.data
    ]


async def set_alerts_paused(user_id: int, paused: bool) -> None:
    get_client().table("users").update({"alerts_paused": paused}).eq("id", user_id).execute()


async def save_user_listing(user_id: int, listing_id: str) -> Optional[bool]:
    """Returns True if newly saved, False if already saved, None if save failed."""
    db = get_client()
    existing = db.table("saved_listings").select("user_id").eq("user_id", user_id).eq("listing_id", listing_id).execute()
    if existing.data:
        return False
    try:
        db.table("saved_listings").insert({"user_id": user_id, "listing_id": listing_id}).execute()
        return True
    except Exception as e:
        logger.warning("Failed to save listing %s for user %d: %s", listing_id, user_id, e)
        return None


async def unsave_user_listing(user_id: int, listing_id: str) -> None:
    get_client().table("saved_listings").delete().eq("user_id", user_id).eq("listing_id", listing_id).execute()


async def update_saved_note(user_id: int, listing_id: str, note: str) -> None:
    get_client().table("saved_listings").update({"note": note}) \
        .eq("user_id", user_id).eq("listing_id", listing_id).execute()


async def get_listing_url(listing_id: str) -> Optional[str]:
    result = get_client().table("listings").select("url").eq("id", listing_id).execute()
    return result.data[0]["url"] if result.data else None


async def get_saved_listings(user_id: int) -> list[dict]:
    result = (
        get_client()
        .table("saved_listings")
        .select("listing_id, saved_at, note, listings(url, city, district, street, price, rooms, area)")
        .eq("user_id", user_id)
        .order("saved_at", desc=True)
        .limit(20)
        .execute()
    )
    return result.data


# ── Admin helpers ──────────────────────────────────────────────────────────────

async def count_users() -> int:
    result = get_client().table("users").select("id", count="exact").execute()
    return result.count or 0


async def count_listings() -> int:
    result = get_client().table("listings").select("id", count="exact").execute()
    return result.count or 0


async def count_active_subscriptions() -> int:
    now = datetime.utcnow().isoformat()
    result = (
        get_client().table("subscriptions")
        .select("id", count="exact")
        .gt("expires_at", now)
        .execute()
    )
    return result.count or 0


async def grant_premium(user_id: int, months: int = 1) -> None:
    """Grant full Pro bundle to a user."""
    from core.models import PRO_FEATURES
    for feature in list(PRO_FEATURES) + ["pro"]:
        await activate_feature(user_id, feature, months=months, stars_paid=0)


async def revoke_all_features(user_id: int) -> None:
    """Remove all subscriptions for a user (downgrade to free)."""
    get_client().table("subscriptions").delete().eq("user_id", user_id).execute()


async def revoke_feature(user_id: int, feature: str) -> None:
    """Remove a specific feature subscription."""
    get_client().table("subscriptions").delete().eq("user_id", user_id).eq("feature", feature).execute()


async def get_all_users() -> list[User]:
    result = get_client().table("users").select("*").order("created_at", desc=True).execute()
    users = []
    for row in result.data:
        features = await _get_active_features(row["id"])
        users.append(_row_to_user(row, features))
    return users


async def get_users_with_feature(feature: str) -> list[User]:
    """Return users who have an active subscription to the given feature."""
    db = get_client()
    now = datetime.utcnow().isoformat()
    subs = (
        db.table("subscriptions")
        .select("user_id")
        .eq("feature", feature)
        .gt("expires_at", now)
        .execute()
    )
    user_ids = list({r["user_id"] for r in subs.data})
    if not user_ids:
        return []
    users_data = db.table("users").select("*").in_("id", user_ids).execute()
    result = []
    for row in users_data.data:
        features = await _get_active_features(row["id"])
        result.append(_row_to_user(row, features))
    return result


async def save_feedback(user_id: int, rating: int) -> str:
    """Returns the new feedback row ID."""
    result = get_client().table("user_feedback").insert({"user_id": user_id, "rating": rating}).execute()
    return result.data[0]["id"]


async def update_feedback_comment(feedback_id: str, comment: str) -> None:
    get_client().table("user_feedback").update({"comment": comment}).eq("id", feedback_id).execute()


async def save_report(user_id: int, listing_id: str, reason: str) -> None:
    get_client().table("listing_reports").insert({
        "user_id": user_id, "listing_id": listing_id, "reason": reason,
    }).execute()
