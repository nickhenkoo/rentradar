from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core.models import CITIES, SERIES
from bot.i18n import t

FEATURE_NAMES: dict[str, dict[str, str]] = {
    "speed":     {"en": "Priority speed",    "ru": "Приоритетная скорость", "lv": "Prioritārais ātrums"},
    "hot":       {"en": "Hot alerts",        "ru": "Горячие объявления",    "lv": "Karstie sludinājumi"},
    "history":   {"en": "Price history",     "ru": "История цен",           "lv": "Cenu vēsture"},
    "analytics": {"en": "Weekly analytics",  "ru": "Еженедельная аналитика","lv": "Iknedēļas analītika"},
    "pro":       {"en": "Pro bundle",        "ru": "Pro пакет",             "lv": "Pro pakete"},
}

# Latvian district names exactly as ss.lv /lv/ pages return them
RIGA_DISTRICTS = [
    "Centrs", "Āgenskalns", "Bolderāja", "Brasa", "Čiekurkalns",
    "Dārzciems", "Daugavgrīva", "Dreiliņi", "Imanta", "Iļģuciems",
    "Jaunciems", "Jugla", "Ķengarags", "Klīversala", "Mežaparks",
    "Mežciems", "Mīlgrāvis", "Pļavnieki", "Purvciems", "Sarkandaugava",
    "Šampēteris-Pleskodāle", "Teika", "Torņakalns", "Vecmīlgrāvis",
    "Vecrīga", "Zasulauks", "Ziepniekkalns", "Zolitūde",
]


def city_keyboard(lang: str) -> InlineKeyboardMarkup:
    # Always show Latvian city names regardless of user language
    buttons = [
        [InlineKeyboardButton(data["lv"], callback_data=f"city_{key}")]
        for key, data in CITIES.items()
    ]
    return InlineKeyboardMarkup(buttons)


def district_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(RIGA_DISTRICTS), 2):
        row = [InlineKeyboardButton(RIGA_DISTRICTS[i], callback_data=f"district_{RIGA_DISTRICTS[i]}")]
        if i + 1 < len(RIGA_DISTRICTS):
            row.append(InlineKeyboardButton(RIGA_DISTRICTS[i + 1], callback_data=f"district_{RIGA_DISTRICTS[i + 1]}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(t("btn_any", lang), callback_data="district_any")])
    return InlineKeyboardMarkup(rows)


def series_keyboard(lang: str) -> InlineKeyboardMarkup:
    keys = list(SERIES.keys())
    rows = []
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(SERIES[keys[i]][lang], callback_data=f"series_{keys[i]}")]
        if i + 1 < len(keys):
            row.append(InlineKeyboardButton(SERIES[keys[i + 1]][lang], callback_data=f"series_{keys[i + 1]}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(t("btn_any", lang), callback_data="series_any")])
    return InlineKeyboardMarkup(rows)


def yes_no_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_yes", lang), callback_data="yn_yes"),
        InlineKeyboardButton(t("btn_no", lang), callback_data="yn_no"),
    ]])


def skip_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_skip", lang), callback_data="skip"),
    ]])


def confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_save", lang), callback_data="confirm"),
        InlineKeyboardButton(t("btn_cancel", lang), callback_data="cancel"),
    ]])


def filter_actions_keyboard(filter_id: str, is_active: bool, lang: str) -> InlineKeyboardMarkup:
    pause_resume = (
        InlineKeyboardButton(t("btn_pause", lang), callback_data=f"filter_pause_{filter_id}")
        if is_active
        else InlineKeyboardButton(t("btn_resume", lang), callback_data=f"filter_resume_{filter_id}")
    )
    return InlineKeyboardMarkup([[
        pause_resume,
        InlineKeyboardButton(t("btn_delete", lang), callback_data=f"filter_delete_{filter_id}"),
    ]])


def subscribe_keyboard(lang: str) -> InlineKeyboardMarkup:
    from core.models import FEATURES
    _suffix = {"en": "€/mo", "ru": "€/мес", "lv": "€/mēn"}.get(lang, "€/mo")
    def _btn(icon, feat, cb):
        name = FEATURE_NAMES[feat].get(lang, FEATURE_NAMES[feat]["en"])
        price = FEATURES[feat]["price_eur"]
        return InlineKeyboardButton(f"{icon} {name} — {price} {_suffix}", callback_data=cb)
    return InlineKeyboardMarkup([
        [_btn("⚡", "speed",     "buy_speed")],
        [_btn("🔥", "hot",       "buy_hot")],
        [_btn("📈", "history",   "buy_history")],
        [_btn("📊", "analytics", "buy_analytics")],
        [_btn("🎯", "pro",       "buy_pro")],
    ])
