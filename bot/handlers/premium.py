from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import core.db as db
from bot.i18n import t


async def price_history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = await db.get_user(query.from_user.id)
    lang = user.language if user else "en"

    if not user or not user.has("history"):
        await context.bot.send_message(
            query.from_user.id,
            t("history_feature_required", lang),
        )
        return

    listing_id = query.data.replace("history_", "")
    points = await db.get_price_history(listing_id)

    if not points:
        await context.bot.send_message(query.from_user.id, t("history_no_data", lang))
        return

    lines = [t("history_header", lang)]
    for p in points:
        date_str = p.recorded_at.strftime("%d.%m.%Y")
        lines.append(t("history_entry", lang, date=date_str, price=p.price))

    await context.bot.send_message(
        query.from_user.id,
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
    )
