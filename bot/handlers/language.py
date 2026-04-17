from telegram import Update
from telegram.ext import ContextTypes
import core.db as db
from bot.i18n import t, lang_keyboard


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await db.get_user(update.effective_user.id)
    lang = user.language if user else "en"
    await update.message.reply_text(
        t("choose_language", lang),
        reply_markup=lang_keyboard(),
    )
