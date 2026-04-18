import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import core.db as db
from bot.i18n import t

logger = logging.getLogger(__name__)

REPORT_REASONS = ["wrong_price", "already_rented", "wrong_info", "spam"]


async def _restore_alert_keyboard(query, user, listing_id: str, lang: str) -> None:
    """Rebuild and restore the original alert keyboard after report flow."""
    listing_url = await db.get_listing_url(listing_id)
    if not listing_url:
        try:
            await query.edit_message_reply_markup(None)
        except Exception:
            pass
        return
    from core.notifier import _localize_url
    from bot.i18n import t as _t
    localized_url = _localize_url(listing_url, lang)
    row1 = [InlineKeyboardButton(_t("btn_view", lang), url=localized_url)]
    if user and user.has("history"):
        row1.append(InlineKeyboardButton(_t("btn_price_history", lang), callback_data=f"history_{listing_id}"))
    row2 = [
        InlineKeyboardButton(_t("btn_save_listing", lang), callback_data=f"save_listing_{listing_id}"),
        InlineKeyboardButton(_t("btn_report", lang), callback_data=f"report_listing|{listing_id}"),
    ]
    try:
        await query.edit_message_reply_markup(InlineKeyboardMarkup([row1, row2]))
    except Exception:
        pass


_FEEDBACK_EMOJIS = {1: "😊", 2: "😐", 3: "😞"}


async def feedback_rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = await db.get_user(query.from_user.id)
    lang = user.language if user else "en"

    # callback: feedback_rate_{1|2|3}
    rating = int(query.data.rsplit("_", 1)[-1])
    feedback_id = await db.save_feedback(query.from_user.id, rating)

    # Ask for optional text comment
    context.user_data["awaiting_feedback_comment"] = {"id": feedback_id, "rating": rating}
    skip_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_skip", lang), callback_data="feedback_comment_skip"),
    ]])
    await query.edit_message_text(t("feedback_comment_prompt", lang), reply_markup=skip_kb)

    log_channel = os.getenv("LOG_CHANNEL_ID")
    if log_channel:
        ref = f"@{query.from_user.username}" if query.from_user.username else str(query.from_user.id)
        emoji = _FEEDBACK_EMOJIS.get(rating, "?")
        try:
            await context.bot.send_message(
                log_channel,
                f"💬 Feedback: {emoji} from {ref}",
            )
        except Exception:
            pass


async def feedback_comment_skip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data.pop("awaiting_feedback_comment", None)
    user = await db.get_user(query.from_user.id)
    lang = user.language if user else "en"
    await query.edit_message_text(t("feedback_thanks", lang))


async def report_listing_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = await db.get_user(query.from_user.id)
    lang = user.language if user else "en"

    # callback: report_listing|{listing_id}
    listing_id = query.data.split("|", 1)[1]

    buttons = [
        [InlineKeyboardButton(t(f"report_{r}", lang), callback_data=f"report_reason|{r}|{listing_id}")]
        for r in REPORT_REASONS
    ]
    buttons.append([InlineKeyboardButton(t("btn_cancel", lang), callback_data=f"report_cancel|{listing_id}")])

    try:
        await query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))
    except Exception:
        await query.message.reply_text(t("report_pick_reason", lang), reply_markup=InlineKeyboardMarkup(buttons))


async def report_reason_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = await db.get_user(query.from_user.id)
    lang = user.language if user else "en"

    # callback: report_reason|{reason}|{listing_id}
    _, reason, listing_id = query.data.split("|", 2)
    await db.save_report(query.from_user.id, listing_id, reason)

    # Restore original alert keyboard
    await _restore_alert_keyboard(query, user, listing_id, lang)
    await query.message.reply_text(t("report_submitted", lang))

    log_channel = os.getenv("LOG_CHANNEL_ID")
    if log_channel:
        ref = f"@{query.from_user.username}" if query.from_user.username else str(query.from_user.id)
        reason_label = t(f"report_{reason}", "en")
        try:
            await context.bot.send_message(
                log_channel,
                f"⚠️ Report from {ref}\n"
                f"Listing: <code>{listing_id}</code>\n"
                f"Reason: {reason_label}",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass


async def report_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    listing_id = query.data.split("|", 1)[1]
    user = await db.get_user(query.from_user.id)
    lang = user.language if user else "en"
    await _restore_alert_keyboard(query, user, listing_id, lang)
