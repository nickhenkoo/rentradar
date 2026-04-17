import logging
import re
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters as tg_filters,
)
from telegram.constants import ParseMode

import core.db as db
from bot.i18n import t
from bot.keyboards import (
    city_keyboard, district_keyboard, series_keyboard,
    yes_no_keyboard, skip_keyboard, confirm_keyboard,
)

logger = logging.getLogger(__name__)

CITY, DISTRICT, PRICE_RANGE, ROOMS_RANGE, AREA_RANGE, FLOOR_RANGE, SERIES, LONG_TERM, LABEL, CONFIRM = range(10)


async def _lang(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> str:
    if "lang" in context.user_data:
        return context.user_data["lang"]
    user = await db.get_user(user_id)
    lang = user.language if user else "en"
    context.user_data["lang"] = lang
    return lang


def _parse_range(text: str) -> tuple[int | None, int | None]:
    """Parse '300-700', '500', '2-4' → (min, max). Returns (None, None) on failure."""
    text = text.strip()
    m = re.match(r'^(\d+)\s*[-–]\s*(\d+)$', text)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return (lo, hi) if lo <= hi else (hi, lo)
    if text.isdigit():
        val = int(text)
        return val, val
    return None, None


async def addfilter_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user = await db.get_or_create_user(update.effective_user)
    lang = user.language
    context.user_data.clear()
    context.user_data["lang"] = lang

    await update.message.reply_text(
        t("ask_city", lang),
        reply_markup=city_keyboard(lang),
    )
    return CITY


async def city_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    city = query.data.replace("city_", "")
    context.user_data["city"] = city
    await query.edit_message_text(
        t("ask_district", lang),
        parse_mode=ParseMode.HTML,
        reply_markup=district_keyboard(lang),
    )
    return DISTRICT


async def district_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    context.user_data["district"] = None if query.data == "district_any" else query.data.replace("district_", "")
    await query.edit_message_text(
        t("ask_price_range", lang), parse_mode=ParseMode.HTML,
        reply_markup=skip_keyboard(lang),
    )
    return PRICE_RANGE


async def price_range_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")
    lo, hi = _parse_range(update.message.text)
    if lo is None:
        await update.message.reply_text(t("invalid_range", lang), parse_mode=ParseMode.HTML)
        return PRICE_RANGE
    context.user_data["price_min"] = lo
    context.user_data["price_max"] = hi
    await update.message.reply_text(
        t("ask_rooms_range", lang), parse_mode=ParseMode.HTML,
        reply_markup=skip_keyboard(lang),
    )
    return ROOMS_RANGE


async def price_range_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    context.user_data["price_min"] = None
    context.user_data["price_max"] = None
    await query.edit_message_text(
        t("ask_rooms_range", lang), parse_mode=ParseMode.HTML,
        reply_markup=skip_keyboard(lang),
    )
    return ROOMS_RANGE


async def rooms_range_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")
    lo, hi = _parse_range(update.message.text)
    if lo is None:
        await update.message.reply_text(t("invalid_range", lang), parse_mode=ParseMode.HTML)
        return ROOMS_RANGE
    context.user_data["rooms_min"] = lo
    context.user_data["rooms_max"] = hi
    await update.message.reply_text(
        t("ask_area_range", lang), parse_mode=ParseMode.HTML,
        reply_markup=skip_keyboard(lang),
    )
    return AREA_RANGE


async def rooms_range_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    context.user_data["rooms_min"] = None
    context.user_data["rooms_max"] = None
    await query.edit_message_text(
        t("ask_area_range", lang), parse_mode=ParseMode.HTML,
        reply_markup=skip_keyboard(lang),
    )
    return AREA_RANGE


async def area_range_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")
    lo, hi = _parse_range(update.message.text)
    if lo is None:
        await update.message.reply_text(t("invalid_range", lang), parse_mode=ParseMode.HTML)
        return AREA_RANGE
    context.user_data["area_min"] = lo
    context.user_data["area_max"] = hi
    await update.message.reply_text(
        t("ask_floor_range", lang), parse_mode=ParseMode.HTML,
        reply_markup=skip_keyboard(lang),
    )
    return FLOOR_RANGE


async def area_range_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    context.user_data["area_min"] = None
    context.user_data["area_max"] = None
    await query.edit_message_text(
        t("ask_floor_range", lang), parse_mode=ParseMode.HTML,
        reply_markup=skip_keyboard(lang),
    )
    return FLOOR_RANGE


async def floor_range_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")
    lo, hi = _parse_range(update.message.text)
    if lo is None:
        await update.message.reply_text(t("invalid_range", lang), parse_mode=ParseMode.HTML)
        return FLOOR_RANGE
    context.user_data["floor_min"] = lo
    context.user_data["floor_max"] = hi
    await update.message.reply_text(
        t("ask_series", lang), parse_mode=ParseMode.HTML,
        reply_markup=series_keyboard(lang),
    )
    return SERIES


async def floor_range_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    context.user_data["floor_min"] = None
    context.user_data["floor_max"] = None
    await query.edit_message_text(
        t("ask_series", lang), parse_mode=ParseMode.HTML,
        reply_markup=series_keyboard(lang),
    )
    return SERIES


async def series_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    context.user_data["series"] = None if query.data == "series_any" else query.data.replace("series_", "")
    await query.edit_message_text(
        t("ask_long_term", lang),
        reply_markup=yes_no_keyboard(lang),
    )
    return LONG_TERM


async def long_term_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    context.user_data["long_term_only"] = query.data == "yn_yes"
    await query.edit_message_text(
        t("ask_label", lang), parse_mode=ParseMode.HTML,
        reply_markup=skip_keyboard(lang),
    )
    return LABEL


async def label_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")
    context.user_data["label"] = update.message.text.strip()
    await _show_preview(update.message.reply_text, context, lang)
    return CONFIRM


async def label_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    context.user_data["label"] = None
    await _show_preview(query.edit_message_text, context, lang)
    return CONFIRM


async def _show_preview(send_fn, context, lang):
    from core.models import Filter
    d = context.user_data
    # Build a temporary Filter to render full_summary
    tmp = Filter(
        id="preview",
        user_id=0,
        city=d.get("city", "riga"),
        label=d.get("label"),
        district=d.get("district"),
        price_min=d.get("price_min"),
        price_max=d.get("price_max"),
        rooms_min=d.get("rooms_min"),
        rooms_max=d.get("rooms_max"),
        area_min=d.get("area_min"),
        area_max=d.get("area_max"),
        floor_min=d.get("floor_min"),
        floor_max=d.get("floor_max"),
        series=d.get("series"),
        long_term_only=d.get("long_term_only", True),
    )
    summary = tmp.full_summary(lang)
    text = t("filter_preview", lang, summary=summary)
    await send_fn(text, parse_mode=ParseMode.HTML, reply_markup=confirm_keyboard(lang))


async def confirm_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    user_id = query.from_user.id
    d = context.user_data

    await db.create_filter(
        user_id=user_id,
        city=d.get("city", "riga"),
        label=d.get("label"),
        district=d.get("district"),
        price_min=d.get("price_min"),
        price_max=d.get("price_max"),
        rooms_min=d.get("rooms_min"),
        rooms_max=d.get("rooms_max"),
        area_min=d.get("area_min"),
        area_max=d.get("area_max"),
        floor_min=d.get("floor_min"),
        floor_max=d.get("floor_max"),
        series=d.get("series"),
        long_term_only=d.get("long_term_only", True),
    )
    await query.edit_message_text(t("filter_saved", lang))
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(t("filter_cancelled", lang))
    else:
        await update.message.reply_text(t("filter_cancelled", lang))
    context.user_data.clear()
    return ConversationHandler.END


def build_addfilter_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("addfilter", addfilter_start)],
        per_message=False,
        states={
            CITY: [CallbackQueryHandler(city_chosen, pattern="^city_")],
            DISTRICT: [CallbackQueryHandler(district_chosen, pattern="^district_")],
            PRICE_RANGE: [
                MessageHandler(tg_filters.TEXT & ~tg_filters.COMMAND, price_range_text),
                CallbackQueryHandler(price_range_skip, pattern="^skip$"),
            ],
            ROOMS_RANGE: [
                MessageHandler(tg_filters.TEXT & ~tg_filters.COMMAND, rooms_range_text),
                CallbackQueryHandler(rooms_range_skip, pattern="^skip$"),
            ],
            AREA_RANGE: [
                MessageHandler(tg_filters.TEXT & ~tg_filters.COMMAND, area_range_text),
                CallbackQueryHandler(area_range_skip, pattern="^skip$"),
            ],
            FLOOR_RANGE: [
                MessageHandler(tg_filters.TEXT & ~tg_filters.COMMAND, floor_range_text),
                CallbackQueryHandler(floor_range_skip, pattern="^skip$"),
            ],
            SERIES: [CallbackQueryHandler(series_chosen, pattern="^series_")],
            LONG_TERM: [CallbackQueryHandler(long_term_chosen, pattern="^yn_")],
            LABEL: [
                MessageHandler(tg_filters.TEXT & ~tg_filters.COMMAND, label_text),
                CallbackQueryHandler(label_skip, pattern="^skip$"),
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm_save, pattern="^confirm$"),
                CallbackQueryHandler(cancel_filter, pattern="^cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_filter),
            CallbackQueryHandler(cancel_filter, pattern="^cancel$"),
        ],
        allow_reentry=True,
    )
