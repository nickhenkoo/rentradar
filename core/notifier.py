import logging
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from core.models import User, Listing, Filter, series_name, city_name, district_name
from bot.i18n import t

_FEEDBACK_PROBABILITY = 1 / 7

logger = logging.getLogger(__name__)

_LANG_TO_SSLV = {"en": "en", "ru": "ru", "lv": "lv"}


def _localize_url(url: str, lang: str) -> str:
    """Replace /en/ prefix in ss.lv URL with the user's language."""
    sslv_lang = _LANG_TO_SSLV.get(lang, "en")
    for prefix in ("/en/", "/ru/", "/lv/"):
        if prefix in url:
            return url.replace(prefix, f"/{sslv_lang}/", 1)
    return url


def _build_alert_text(user: User, listing: Listing, f: Filter, is_hot: bool = False) -> str:
    lang = user.language
    district = listing.district or ""

    lines = []

    if is_hot:
        lines.append(t("alert_hot_prefix", lang))

    if district:
        lines.append(t("alert_header", lang, city=city_name(listing.city, lang), district=district_name(district, lang)))
    else:
        lines.append(t("alert_header_no_dist", lang, city=city_name(listing.city, lang)))

    if listing.street:
        lines.append(f"📍 {listing.street}")

    lines.append("")

    if listing.price:
        lines.append(t("alert_price", lang, price=listing.price))
    else:
        lines.append(t("alert_no_price", lang))

    if listing.rooms or listing.area:
        rooms = listing.rooms or "?"
        area = listing.area or "?"
        lines.append(t("alert_details", lang, rooms=rooms, area=area))

    if listing.floor and listing.floor_total:
        lines.append(t("alert_floor", lang, floor=listing.floor, floor_total=listing.floor_total))

    if listing.series:
        lines.append(t("alert_series", lang, series=series_name(listing.series, lang)))

    lines.append("")
    lines.append(t("alert_matched_filter", lang, filter_name=f.display_name(lang)))
    lines.append("")
    lines.append(t("alert_filter_summary", lang, filter_summary=f.full_summary(lang)))

    return "\n".join(lines)


def _build_keyboard(user: User, listing: Listing, lang: str) -> InlineKeyboardMarkup:
    listing_url = _localize_url(listing.url, lang)
    row1 = [InlineKeyboardButton(t("btn_view", lang), url=listing_url)]
    if user.has("history"):
        row1.append(InlineKeyboardButton(t("btn_price_history", lang), callback_data=f"history_{listing.id}"))
    row2 = [
        InlineKeyboardButton(t("btn_save_listing", lang), callback_data=f"save_listing_{listing.id}"),
        InlineKeyboardButton(t("btn_report", lang), callback_data=f"report_listing|{listing.id}"),
    ]
    return InlineKeyboardMarkup([row1, row2])


async def send_alert(bot, user: User, listing: Listing, f: Filter, is_hot: bool = False) -> None:
    lang = user.language
    text = _build_alert_text(user, listing, f, is_hot)
    keyboard = _build_keyboard(user, listing, lang)

    sent = False
    if listing.image_urls:
        try:
            await bot.send_photo(
                chat_id=user.id,
                photo=listing.image_urls[0],
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
            sent = True
        except Exception as e:
            logger.warning("send_photo failed for user %d (%s), falling back to text: %s", user.id, listing.id, e)

    if not sent:
        try:
            await bot.send_message(
                chat_id=user.id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.error("Failed to send alert to user %d: %s", user.id, e)
            return

    if random.random() < _FEEDBACK_PROBABILITY:
        feedback_keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("😊", callback_data="feedback_rate_1"),
            InlineKeyboardButton("😐", callback_data="feedback_rate_2"),
            InlineKeyboardButton("😞", callback_data="feedback_rate_3"),
        ]])
        try:
            await bot.send_message(
                chat_id=user.id,
                text=t("feedback_prompt", lang),
                reply_markup=feedback_keyboard,
            )
        except Exception as e:
            logger.warning("Failed to send feedback prompt to user %d: %s", user.id, e)
