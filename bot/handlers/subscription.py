import logging
from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import core.db as db
from bot.i18n import t
from bot.keyboards import subscribe_keyboard, FEATURE_NAMES
from core.models import FEATURES, PRO_FEATURES

logger = logging.getLogger(__name__)


def _feature_name(feature: str, lang: str) -> str:
    return FEATURE_NAMES.get(feature, {}).get(lang, feature)


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await db.get_user(update.effective_user.id)
    lang = user.language if user else "en"
    await update.message.reply_text(
        t("subscribe_intro", lang),
        parse_mode=ParseMode.HTML,
        reply_markup=subscribe_keyboard(lang),
    )


async def buy_feature_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = await db.get_user(query.from_user.id)
    lang = user.language if user else "en"

    feature = query.data.replace("buy_", "")
    if feature not in FEATURES:
        return

    info = FEATURES[feature]
    fname = _feature_name(feature, lang)

    # Check if already active
    if user and user.has(feature):
        subs = await db.get_user_subscriptions(query.from_user.id)
        for s in subs:
            if s["feature"] == feature or (feature == "pro" and s["feature"] in PRO_FEATURES):
                from datetime import datetime
                exp = s.get("expires_at", "")
                try:
                    dt = datetime.fromisoformat(exp.replace("Z", "+00:00")).replace(tzinfo=None)
                    date_str = dt.strftime("%d.%m.%Y")
                except Exception:
                    date_str = "?"
                await query.edit_message_text(t("already_have_feature", lang, feature=fname, date=date_str))
                return

    await context.bot.send_invoice(
        chat_id=query.from_user.id,
        title=fname,
        description=f"RentRadar {fname} — 1 month",
        payload=f"feature_{feature}",
        currency="XTR",
        prices=[LabeledPrice(label=fname, amount=info["price_stars"])],
    )


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.pre_checkout_query.answer(ok=True)


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.language if user else "en"

    payload = update.message.successful_payment.invoice_payload
    stars = update.message.successful_payment.total_amount
    feature = payload.replace("feature_", "")

    await db.activate_feature(user_id, feature, months=1, stars_paid=stars)

    user_refreshed = await db.get_user(user_id)
    fname = _feature_name(feature, lang)
    subs = await db.get_user_subscriptions(user_id)
    date_str = "?"
    for s in subs:
        if s["feature"] == feature:
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(s["expires_at"].replace("Z", "+00:00")).replace(tzinfo=None)
                date_str = dt.strftime("%d.%m.%Y")
            except Exception:
                pass
            break

    await update.message.reply_text(t("payment_success", lang, feature=fname, date=date_str))


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from datetime import datetime
    from core.models import PRO_FEATURES

    user = await db.get_user(update.effective_user.id)
    lang = user.language if user else "en"

    subs = await db.get_user_subscriptions(update.effective_user.id)
    active = {s["feature"]: s["expires_at"] for s in subs}

    # Determine current plan for top-of-message summary
    plan_str = t("status_plan_pro", lang) if "pro" in active else t("status_plan_free", lang)

    lines = [
        t("status_header", lang),
        t("status_plan_label", lang, plan=plan_str),
        "",
    ]

    all_features = ["speed", "hot", "history", "analytics", "pro"]
    for feature in all_features:
        fname = _feature_name(feature, lang)
        if feature in active:
            try:
                dt = datetime.fromisoformat(active[feature].replace("Z", "+00:00")).replace(tzinfo=None)
                date_str = dt.strftime("%d.%m.%Y")
            except Exception:
                date_str = "?"
            lines.append(t("status_feature_active", lang, feature=fname, date=date_str))
        else:
            lines.append(t("status_feature_inactive", lang, feature=fname))

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
