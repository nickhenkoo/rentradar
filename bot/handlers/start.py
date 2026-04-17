from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import core.db as db
from bot.i18n import t, lang_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await db.get_or_create_user(update.effective_user)
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
