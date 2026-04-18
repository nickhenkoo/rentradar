import os
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import core.db as db
from bot.i18n import t, lang_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    _, is_new = await db.get_or_create_user(user)
    if is_new:
        log_channel = os.getenv("LOG_CHANNEL_ID")
        if log_channel:
            name = user.full_name
            username = f" @{user.username}" if user.username else ""
            await context.bot.send_message(
                log_channel,
                f"👤 New user: <b>{name}</b>{username} (<code>{user.id}</code>)",
                parse_mode=ParseMode.HTML,
            )
    await update.message.reply_text(
        t("choose_language", "en"),
        reply_markup=lang_keyboard(),
    )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    lang_map = {"lang_en": "en", "lang_ru": "ru", "lang_lv": "lv"}
    lang = lang_map.get(query.data, "en")
    await db.update_user_language(query.from_user.id, lang)
    await query.edit_message_text(t("language_set", lang))
    await context.bot.send_message(query.from_user.id, t("welcome", lang), parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await db.get_user(update.effective_user.id)
    lang = user.language if user else "en"
    await update.message.reply_text(t("help", lang), parse_mode=ParseMode.HTML)
