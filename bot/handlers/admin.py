import os
import logging
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import core.db as db
from bot.i18n import t

logger = logging.getLogger(__name__)


def _admin_id() -> int | None:
    val = os.environ.get("ADMIN_ID")
    return int(val) if val else None


def _is_admin(user_id: int) -> bool:
    aid = _admin_id()
    return aid is not None and user_id == aid


def _require_admin(func):
    import functools
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _is_admin(update.effective_user.id):
            return
        return await func(update, context)
    return wrapper


@_require_admin
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_count = await db.count_users()
    listing_count = await db.count_listings()
    active_subs = await db.count_active_subscriptions()

    scheduler = context.application.bot_data.get("scheduler")
    parser_status = "running" if scheduler and scheduler.running else "stopped"
    last_run = context.application.bot_data.get("last_parse_time")
    last_run_str = last_run.strftime("%d.%m %H:%M") if last_run else "never"

    text = (
        f"<b>Admin Panel</b>\n\n"
        f"👥 Users: <b>{user_count}</b>\n"
        f"🏠 Listings: <b>{listing_count}</b>\n"
        f"⭐ Active subs: <b>{active_subs}</b>\n"
        f"⚙️ Parser: <b>{parser_status}</b>\n"
        f"🕐 Last parse: <b>{last_run_str}</b>\n\n"
        f"Commands:\n"
        f"/admin_broadcast — send message to all users\n"
        f"/admin_grant &lt;user_id&gt; [months] — grant Pro\n"
        f"/admin_setplan &lt;user_id&gt; &lt;free|pro|feature&gt; [months] — change plan\n"
        f"/admin_user &lt;user_id&gt; — view user info\n"
        f"/admin_stats — detailed analytics\n"
        f"/admin_refresh — clear sent_alerts (force re-notify)\n\n"
        f"<b>Feature testing:</b>\n"
        f"/admin_test_alerts — 5 alerts + seed price history\n"
        f"/admin_test_hot — send one 🔥 hot alert\n"
        f"/admin_test_analytics — trigger analytics report now\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


@_require_admin
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_client = db.get_client()

    # Top cities from filters
    filters_result = db_client.table("filters").select("city").eq("is_active", True).execute()
    city_counts: dict[str, int] = {}
    for row in filters_result.data:
        city = row.get("city", "unknown")
        city_counts[city] = city_counts.get(city, 0) + 1

    top_cities = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    cities_str = "\n".join(f"  {c}: {n}" for c, n in top_cities) or "  —"

    # Average budget from filters with price_max
    prices_result = db_client.table("filters").select("price_max").not_.is_("price_max", "null").execute()
    prices = [r["price_max"] for r in prices_result.data if r["price_max"]]
    avg_budget = int(sum(prices) / len(prices)) if prices else 0

    # Paused users
    paused = db_client.table("users").select("id", count="exact").eq("alerts_paused", True).execute()
    paused_count = paused.count or 0

    # Active filters
    active_filters = db_client.table("filters").select("id", count="exact").eq("is_active", True).execute()
    active_filters_count = active_filters.count or 0

    avg_budget_str = f"{avg_budget} €" if avg_budget else "n/a"
    text = (
        f"<b>Analytics</b>\n\n"
        f"🏙 Top cities (active filters):\n{cities_str}\n\n"
        f"💶 Avg price ceiling: <b>{avg_budget_str}</b>\n"
        f"📋 Active filters: <b>{active_filters_count}</b>\n"
        f"⏸ Users with paused alerts: <b>{paused_count}</b>\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


@_require_admin
async def admin_grant(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /admin_grant &lt;user_id&gt; [months]", parse_mode=ParseMode.HTML)
        return
    try:
        target_id = int(args[0])
        months = int(args[1]) if len(args) > 1 else 1
    except ValueError:
        await update.message.reply_text("Invalid user_id or months.")
        return

    await db.grant_premium(target_id, months=months)
    await update.message.reply_text(f"✅ Pro bundle granted to user {target_id} for {months} month(s).")


@_require_admin
async def admin_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /admin_user &lt;user_id&gt;", parse_mode=ParseMode.HTML)
        return
    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("Invalid user_id.")
        return

    user = await db.get_user(target_id)
    if not user:
        await update.message.reply_text(f"User {target_id} not found.")
        return

    user_filters = await db.get_user_filters(target_id)
    subs = await db.get_user_subscriptions(target_id)

    name = user.first_name or user.username or str(user.id)
    active_features = ", ".join(user._active_features) if user._active_features else "none"
    paused_str = "yes" if user.alerts_paused else "no"
    filter_lines = []
    for f in user_filters:
        status = "✅" if f.is_active else "⏸"
        filter_lines.append(f"  {status} {f.display_name(user.language)}")
    filters_str = "\n".join(filter_lines) or "  none"

    sub_lines = []
    for s in subs:
        try:
            dt = datetime.fromisoformat(s["expires_at"].replace("Z", "+00:00")).replace(tzinfo=None)
            exp = dt.strftime("%d.%m.%Y")
        except Exception:
            exp = "?"
        sub_lines.append(f"  {s['feature']} until {exp}")
    subs_str = "\n".join(sub_lines) or "  none"

    text = (
        f"<b>User {target_id}</b>\n"
        f"Name: {name}\n"
        f"Language: {user.language}\n"
        f"Alerts paused: {paused_str}\n"
        f"Active features: {active_features}\n\n"
        f"<b>Filters:</b>\n{filters_str}\n\n"
        f"<b>Subscriptions:</b>\n{subs_str}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


@_require_admin
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usage: /admin_broadcast <message text>"""
    if not context.args:
        await update.message.reply_text("Usage: /admin_broadcast &lt;message&gt;", parse_mode=ParseMode.HTML)
        return

    msg = " ".join(context.args)
    users = await db.get_all_users()
    sent = 0
    failed = 0
    for user in users:
        try:
            await context.bot.send_message(user.id, msg)
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(f"Broadcast done. Sent: {sent}, failed: {failed}.")


@_require_admin
async def admin_test_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send up to 5 test alerts to the admin.
    Prefers real listings from the DB so View and Save work correctly.
    Falls back to fake listings (which are inserted into DB so saves work).
    """
    from core.models import Listing, Filter
    from core.notifier import send_alert

    admin_id = _admin_id()
    user = await db.get_user(admin_id)
    if not user:
        await update.message.reply_text("Admin user not found in DB. Send /start first.")
        return

    test_filter = Filter(
        id="test", user_id=admin_id, city="riga",
        label="Test filter", district="Centrs",  # matches DISTRICTS key
        price_min=300, price_max=700,
    )

    # Use real listings from DB so View URLs and Save both work
    db_client = db.get_client()
    rows = db_client.table("listings").select("*").limit(5).execute()

    test_listings: list[Listing] = []

    if rows.data:
        for row in rows.data:
            test_listings.append(Listing(
                id=row["id"],
                source=row.get("source", "sslv"),
                url=row["url"],
                city=row.get("city", "riga"),
                title=row.get("title"),
                district=row.get("district"),
                street=row.get("street"),
                price=row.get("price"),
                rooms=row.get("rooms"),
                area=row.get("area"),
                floor=row.get("floor"),
                floor_total=row.get("floor_total"),
                series=row.get("series"),
                is_long_term=row.get("is_long_term", True),
                image_urls=row.get("image_urls") or [],
            ))
    else:
        # DB empty — create fake listings and insert them so FK allows saves
        for i in range(1, 6):
            listing = Listing(
                id=f"test_{i}",
                source="sslv",
                url=f"https://www.ss.lv/lv/real-estate/flats/riga/centre/test{i:08d}.html",
                city="riga",
                title=f"Test listing {i}",
                district="Centrs",
                street="Brīvības iela 1",
                price=400 + i * 50,
                rooms=i,
                area=40 + i * 10,
                floor=i,
                floor_total=9,
                series="602",
                is_long_term=True,
            )
            await db.save_listing(listing)  # insert so saves work
            test_listings.append(listing)

    for i, listing in enumerate(test_listings, start=1):
        await send_alert(context.bot, user, listing, test_filter, is_hot=(i == 1))

    # Seed price history entries starting from now, going back a few hours
    # (simulates recheck cycles that happened today — no dates before the listing existed)
    now = datetime.utcnow()
    for listing in test_listings:
        if listing.price:
            base = listing.price
            for hours_ago, delta in [(3, 0), (2, +20), (0, -15)]:
                try:
                    db.get_client().table("price_history").insert({
                        "listing_id": listing.id,
                        "price": base + delta,
                        "recorded_at": (now - timedelta(hours=hours_ago)).isoformat(),
                    }).execute()
                except Exception:
                    pass

    await update.message.reply_text(
        f"✅ {len(test_listings)} test alerts sent "
        f"({'real DB listings' if rows.data else 'fake listings'}).\n\n"
        f"Price history seeded for each listing.\n"
        f"Click <b>Price history</b> on any alert to test it.",
        parse_mode="HTML",
    )


@_require_admin
async def admin_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear sent_alerts for admin to re-receive recent listings (for testing)."""
    db_client = db.get_client()
    admin_id = _admin_id()
    db_client.table("sent_alerts").delete().eq("user_id", admin_id).execute()
    await update.message.reply_text("✅ Your sent_alerts cleared. You'll re-receive next matches.")


@_require_admin
async def admin_setplan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Usage:
      /admin_setplan <user_id> free             — revoke all subscriptions
      /admin_setplan <user_id> pro [months]     — grant full Pro bundle
      /admin_setplan <user_id> <feature> [months] — grant specific feature
                     (speed | hot | history | analytics)
    """
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: /admin_setplan &lt;user_id&gt; &lt;free|pro|speed|hot|history|analytics&gt; [months]",
            parse_mode="HTML",
        )
        return

    try:
        target_id = int(args[0])
        plan = args[1].lower()
        months = int(args[2]) if len(args) > 2 else 1
    except ValueError:
        await update.message.reply_text("Invalid arguments.")
        return

    valid_plans = {"free", "pro", "speed", "hot", "history", "analytics"}
    if plan not in valid_plans:
        await update.message.reply_text(
            f"Unknown plan '{plan}'. Valid: free, pro, speed, hot, history, analytics"
        )
        return

    user = await db.get_user(target_id)
    if not user:
        await update.message.reply_text(f"User {target_id} not found.")
        return

    if plan == "free":
        await db.revoke_all_features(target_id)
        await update.message.reply_text(f"✅ User {target_id} downgraded to Free plan.")
    elif plan == "pro":
        # Revoke first so the new grant sets a fresh expiry (not an extension)
        await db.revoke_all_features(target_id)
        await db.grant_premium(target_id, months=months)
        await update.message.reply_text(
            f"✅ Pro bundle set for user {target_id} for {months} month(s) from now."
        )
    else:
        # Revoke only this feature so months count from today, not from old expiry
        await db.revoke_feature(target_id, plan)
        await db.activate_feature(target_id, plan, months=months, stars_paid=0)
        await update.message.reply_text(
            f"✅ Feature '{plan}' granted to user {target_id} for {months} month(s)."
        )


@_require_admin
async def admin_test_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger weekly analytics report for admin right now (no need to wait for Monday)."""
    from core.analytics import _build_analytics

    admin_id = _admin_id()
    user = await db.get_user(admin_id)
    if not user:
        await update.message.reply_text("Admin user not found. Send /start first.")
        return

    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    db_client = db.get_client()
    result = (
        db_client.table("listings")
        .select("city, price, rooms, district")
        .gt("first_seen", week_ago)
        .neq("is_long_term", False)
        .execute()
    )

    count = len(result.data)
    text = _build_analytics(user, result.data)
    await context.bot.send_message(admin_id, text, parse_mode="HTML")
    await update.message.reply_text(f"✅ Analytics sent ({count} listings from past 7 days).")


@_require_admin
async def admin_test_hot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send one test hot-listing alert to admin.
    Picks the cheapest real listing vs median in its city+rooms bucket,
    or sends a forced-hot fake if no real listings exist.
    """
    from core.models import Listing, Filter
    from core.notifier import send_alert

    admin_id = _admin_id()
    user = await db.get_user(admin_id)
    if not user:
        await update.message.reply_text("Admin user not found. Send /start first.")
        return

    test_filter = Filter(
        id="test_hot", user_id=admin_id, city="riga",
        label="Hot test", price_min=None, price_max=None,
    )

    # Try to find the cheapest real listing to use as the "hot" one
    db_client = db.get_client()
    rows = db_client.table("listings").select("*").not_.is_("price", "null").order("price").limit(1).execute()

    if rows.data:
        row = rows.data[0]
        listing = Listing(
            id=row["id"], source=row.get("source", "sslv"), url=row["url"],
            city=row.get("city", "riga"), title=row.get("title"),
            district=row.get("district"), street=row.get("street"),
            price=row.get("price"), rooms=row.get("rooms"), area=row.get("area"),
            floor=row.get("floor"), floor_total=row.get("floor_total"),
            series=row.get("series"), is_long_term=row.get("is_long_term", True),
            image_urls=row.get("image_urls") or [],
        )
    else:
        listing = Listing(
            id="test_hot_1", source="sslv",
            url="https://www.ss.lv/lv/real-estate/flats/riga/centre/test00000001.html",
            city="riga", district="Centrs", street="Brīvības iela 1",
            price=299, rooms=2, area=52, floor=3, floor_total=9, series="602",
            is_long_term=True,
        )
        await db.save_listing(listing)

    # Force is_hot=True regardless of subscription gate (this is a test command)
    await send_alert(context.bot, user, listing, test_filter, is_hot=True)
    await update.message.reply_text(
        f"✅ Hot alert sent for listing <code>{listing.id}</code> · {listing.price} €",
        parse_mode="HTML",
    )
