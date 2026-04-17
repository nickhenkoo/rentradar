import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, filters as tg_filters
from telegram.constants import ParseMode

import core.db as db
from bot.i18n import t
from bot.keyboards import filter_actions_keyboard
from core.notifier import _localize_url
from core.models import district_name

logger = logging.getLogger(__name__)


async def myfilters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.language if user else "en"

    user_filters = await db.get_user_filters(user_id)
    if not user_filters:
        await update.message.reply_text(t("no_filters", lang))
        return

    await update.message.reply_text(t("your_filters", lang), parse_mode=ParseMode.HTML)

    for n, f in enumerate(user_filters, start=1):
        label = f.label or f.city.capitalize()
        city = f.city.capitalize()
        district = district_name(f.district, lang) if f.district else t("any", lang)
        price_max = str(f.price_max) if f.price_max else t("any", lang)
        rooms_min = str(f.rooms_min) if f.rooms_min else t("any", lang)

        status = "" if f.is_active else " ⏸"
        text = t(
            "filter_item", lang,
            n=n,
            label=label + status,
            city=city,
            district=district,
            price_max=price_max,
            rooms_min=rooms_min,
        )
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=filter_actions_keyboard(f.id, f.is_active, lang),
        )


async def filter_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = await db.get_user(user_id)
    lang = user.language if user else "en"

    filter_id = query.data.replace("filter_delete_", "")
    await db.delete_filter(filter_id, user_id)
    await query.edit_message_text(t("filter_deleted", lang))


async def filter_pause_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = await db.get_user(user_id)
    lang = user.language if user else "en"

    filter_id = query.data.replace("filter_pause_", "")
    await db.set_filter_active(filter_id, user_id, False)
    await query.edit_message_reply_markup(reply_markup=None)
    await context.bot.send_message(user_id, t("filter_paused", lang))


async def filter_resume_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = await db.get_user(user_id)
    lang = user.language if user else "en"

    filter_id = query.data.replace("filter_resume_", "")
    await db.set_filter_active(filter_id, user_id, True)
    await query.edit_message_reply_markup(reply_markup=None)
    await context.bot.send_message(user_id, t("filter_resumed", lang))


async def pause_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.language if user else "en"
    if user and user.alerts_paused:
        await update.message.reply_text(t("alerts_already_paused", lang))
        return
    await db.set_alerts_paused(user_id, True)
    await update.message.reply_text(t("alerts_paused_msg", lang))


async def resume_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.language if user else "en"
    if user and not user.alerts_paused:
        await update.message.reply_text(t("alerts_already_active", lang))
        return
    await db.set_alerts_paused(user_id, False)
    await update.message.reply_text(t("alerts_resumed_msg", lang))


async def saved_listings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.language if user else "en"

    rows = await db.get_saved_listings(user_id)
    if not rows:
        await update.message.reply_text(t("no_saved_listings", lang))
        return

    await update.message.reply_text(t("saved_listings_header", lang), parse_mode=ParseMode.HTML)
    for row in rows:
        listing = row.get("listings") or {}
        listing_id = row.get("listing_id", "")
        note = row.get("note") or ""
        city = listing.get("city", "")
        district = listing.get("district", "")
        street = listing.get("street", "")
        price = listing.get("price")
        rooms = listing.get("rooms")
        area = listing.get("area")
        url = _localize_url(listing.get("url", ""), lang)

        parts = []
        if district:
            parts.append(district_name(district, lang))
        if street:
            parts.append(street)
        location = ", ".join(parts) if parts else city
        price_str = f"{price} €" if price else "—"
        details = []
        if rooms:
            details.append(f"{rooms} {t('rooms', lang).lower()}")
        if area:
            details.append(f"{area} m²")
        detail_str = " · ".join(details) if details else ""

        text = f"🏠 <b>{location}</b>"
        if detail_str:
            text += f"\n{detail_str}"
        text += f"\n💶 {price_str}"
        if note:
            text += f"\n📝 <i>{note}</i>"

        note_btn_key = "btn_edit_note" if note else "btn_add_note"
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(t("btn_view", lang), url=url),
                InlineKeyboardButton(t("btn_unsave_listing", lang), callback_data=f"unsave_listing_{listing_id}"),
            ],
            [InlineKeyboardButton(t(note_btn_key, lang), callback_data=f"note_listing_{listing_id}")],
        ] if listing_id else [
            [InlineKeyboardButton(t("btn_view", lang), url=url)],
        ])
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def save_listing_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = await db.get_user(user_id)
    lang = user.language if user else "en"

    listing_id = query.data.replace("save_listing_", "")
    result = await db.save_user_listing(user_id, listing_id)

    if result is True:
        await context.bot.send_message(user_id, t("listing_saved", lang))
        # Update keyboard: replace Save button with Unsave button
        listing_url = await db.get_listing_url(listing_id)
        if listing_url:
            localized_url = _localize_url(listing_url, lang)
            new_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(t("btn_view", lang), url=localized_url)],
                [InlineKeyboardButton(t("btn_unsave_listing", lang), callback_data=f"unsave_listing_{listing_id}")],
            ])
            try:
                await query.edit_message_reply_markup(reply_markup=new_keyboard)
            except Exception:
                pass
    elif result is False:
        await context.bot.send_message(user_id, t("listing_already_saved", lang))
    else:
        await context.bot.send_message(user_id, t("listing_save_error", lang))


async def unsave_listing_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = await db.get_user(user_id)
    lang = user.language if user else "en"

    listing_id = query.data.replace("unsave_listing_", "")
    await db.unsave_user_listing(user_id, listing_id)
    await context.bot.send_message(user_id, t("listing_unsaved", lang))

    # Restore Save button in the keyboard
    listing_url = await db.get_listing_url(listing_id)
    if listing_url:
        localized_url = _localize_url(listing_url, lang)
        restored_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t("btn_view", lang), url=localized_url)],
            [InlineKeyboardButton(t("btn_save_listing", lang), callback_data=f"save_listing_{listing_id}")],
        ])
        try:
            await query.edit_message_reply_markup(reply_markup=restored_keyboard)
        except Exception:
            pass


async def note_listing_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = await db.get_user(user_id)
    lang = user.language if user else "en"

    listing_id = query.data.replace("note_listing_", "")
    context.user_data["awaiting_note_for"] = listing_id
    await context.bot.send_message(user_id, t("note_prompt", lang))


async def note_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    listing_id = context.user_data.get("awaiting_note_for")
    if not listing_id:
        return
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.language if user else "en"

    text = update.message.text.strip()
    if len(text) > 200:
        await update.message.reply_text(t("note_too_long", lang))
        return  # keep awaiting_note_for so user can retry

    context.user_data.pop("awaiting_note_for")
    await db.update_saved_note(user_id, listing_id, text)
    await update.message.reply_text(t("note_saved", lang))


async def cancel_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = await db.get_user(user_id)
    lang = user.language if user else "en"

    context.user_data.pop("awaiting_note_for", None)
    await update.message.reply_text(t("note_cancelled", lang))
