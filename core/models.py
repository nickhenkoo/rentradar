from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# ── Geography ──────────────────────────────────────────────────────────────────

CITIES: dict[str, dict[str, str]] = {
    "riga":        {"en": "Riga",        "ru": "Рига",        "lv": "Rīga"},
    "jurmala":     {"en": "Jūrmala",     "ru": "Юрмала",      "lv": "Jūrmala"},
    "daugavpils":  {"en": "Daugavpils",  "ru": "Даугавпилс",  "lv": "Daugavpils"},
    "liepaja":     {"en": "Liepāja",     "ru": "Лиепая",      "lv": "Liepāja"},
    "jelgava":     {"en": "Jelgava",     "ru": "Елгава",      "lv": "Jelgava"},
    "ventspils":   {"en": "Ventspils",   "ru": "Вентспилс",   "lv": "Ventspils"},
    "rezekne":     {"en": "Rēzekne",     "ru": "Резекне",     "lv": "Rēzekne"},
    "jekabpils":   {"en": "Jēkabpils",   "ru": "Екабпилс",    "lv": "Jēkabpils"},
    "valmiera":    {"en": "Valmiera",    "ru": "Валмиера",    "lv": "Valmiera"},
    "ogre":        {"en": "Ogre",        "ru": "Огре",        "lv": "Ogre"},
}


def city_name(city_key: str, lang: str) -> str:
    return CITIES.get(city_key, {}).get(lang, city_key.capitalize())


# ── Building series ────────────────────────────────────────────────────────────

SERIES: dict[str, dict[str, str]] = {
    "103":            {"en": "103 series",         "ru": "103 серия",          "lv": "103. sērija"},
    "104":            {"en": "104 series",         "ru": "104 серия",          "lv": "104. sērija"},
    "119":            {"en": "119 series",         "ru": "119 серия",          "lv": "119. sērija"},
    "467":            {"en": "467 series",         "ru": "467 серия",          "lv": "467. sērija"},
    "602":            {"en": "602 series",         "ru": "602 серия",          "lv": "602. sērija"},
    "brezhnevka":     {"en": "Brezhnevka",         "ru": "Брежневка",          "lv": "Brežņevka"},
    "khrushchevka":   {"en": "Khrushchevka",       "ru": "Хрущёвка",           "lv": "Hrušcovka"},
    "czech":          {"en": "Czech project",      "ru": "Чешский проект",     "lv": "Čehu projekts"},
    "french":         {"en": "French project",     "ru": "Французский проект", "lv": "Franču projekts"},
    "lithuanian_new": {"en": "Lithuanian new",     "ru": "Лит. новый проект",  "lv": "Lietuviešu jaunais"},
    "lithuanian_old": {"en": "Lithuanian old",     "ru": "Лит. старый проект", "lv": "Lietuviešu vecais"},
    "small_family":   {"en": "Small family",       "ru": "Малосемейка",        "lv": "Mazģimenes"},
    "prewar":         {"en": "Pre-war building",   "ru": "Довоенный дом",      "lv": "Pirmskara māja"},
    "stalinka":       {"en": "Stalinka",           "ru": "Сталинка",           "lv": "Staļinka"},
    "special":        {"en": "Special project",    "ru": "Спецпроект",         "lv": "Speciālprojekts"},
    "new":            {"en": "New project",        "ru": "Новостройка",        "lv": "Jaunbūve"},
    "wooden":         {"en": "Wooden building",    "ru": "Деревянный дом",     "lv": "Koka māja"},
    "brick":          {"en": "Brick building",     "ru": "Кирпичный дом",      "lv": "Ķieģeļu māja"},
}


def series_name(series_key: str, lang: str) -> str:
    return SERIES.get(series_key, {}).get(lang, series_key)


# ── District translations ──────────────────────────────────────────────────────
# Keyed by Latvian ss.lv label (parsed from /lv/ URLs).
# "en" value = display name for English users (proper capitalisation).

DISTRICTS: dict[str, dict[str, str]] = {
    # Latvian key (as parsed from ss.lv /lv/ URLs)   EN display          RU display
    "Centrs":                   {"en": "Centre",                    "ru": "Центр"},
    "Āgenskalns":               {"en": "Agenskalns",                "ru": "Агенскалнс"},
    "Purvciems":                {"en": "Purvciems",                 "ru": "Пурвциемс"},
    "Imanta":                   {"en": "Imanta",                    "ru": "Иманта"},
    "Šampēteris-Pleskodāle":   {"en": "Shampeteris-Pleskodale",    "ru": "Шампетерис-Плескодале"},
    "Vecrīga":                  {"en": "Vecriga",                   "ru": "Вецрига"},
    "Iļģuciems":                {"en": "Ilguciems",                 "ru": "Ильгюциемс"},
    "Pļavnieki":                {"en": "Plyavnieki",                "ru": "Плявниеки"},
    "Šķirotava":                {"en": "Shkirotava",                "ru": "Шкиротава"},
    "Krasta ielas r-ns":        {"en": "Krasta st. area",           "ru": "р-н ул. Краста"},
    "Vecmīlgrāvis":             {"en": "Vecmilgravis",              "ru": "Вецмилгравис"},
    "Ķengarags":                {"en": "Kengarags",                 "ru": "Кенгарагс"},
    "Teika":                    {"en": "Teika",                     "ru": "Тейка"},
    "Mežciems":                 {"en": "Mezciems",                  "ru": "Межциемс"},
    "Bolderāja":                {"en": "Bolderaja",                 "ru": "Болдерая"},
    "Jugla":                    {"en": "Jugla",                     "ru": "Югла"},
    "Zolitūde":                 {"en": "Zolitude",                  "ru": "Золитуде"},
    "Dārzciems":                {"en": "Darzciems",                 "ru": "Дарзциемс"},
    "Jaunciems":                {"en": "Jaunciems",                 "ru": "Яунциемс"},
    "Mīlgrāvis":                {"en": "Milgravis",                 "ru": "Милгравис"},
    "Brasa":                    {"en": "Brasa",                     "ru": "Браса"},
    "Sarkandaugava":            {"en": "Sarkandaugava",             "ru": "Саркандаугава"},
    "Mežaparks":                {"en": "Mezaparks",                 "ru": "Межапаркс"},
    "Daugavgrīva":              {"en": "Daugavgriva",               "ru": "Даугавгрива"},
    "Zasulauks":                {"en": "Zasulauks",                 "ru": "Засулаукс"},
    "Pleskodāle":               {"en": "Pleskodale",                "ru": "Плескодале"},
    "Klīversala":               {"en": "Kliversala",                "ru": "Кливерсала"},
    "Sulakalns":                {"en": "Sulakalns",                 "ru": "Сулакалнс"},
    "Dreiliņi":                 {"en": "Dreiliņi",                  "ru": "Дрейлини"},
    "Berģi":                    {"en": "Bergi",                     "ru": "Берги"},
    "Čiekurkalns":              {"en": "Chiekurkalns",              "ru": "Чиекуркалнс"},
    "Torņakalns":               {"en": "Tornakalns",                "ru": "Торнакалнс"},
    "Ziepniekkalns":            {"en": "Ziepniekkalns",             "ru": "Зиепниеккалнс"},
}


def district_name(district: str, lang: str) -> str:
    """Return translated district name. LV users see the native Latvian name as-is."""
    if lang == "lv":
        return district
    # Exact lookup first, then case-insensitive fallback
    entry = DISTRICTS.get(district)
    if entry is None:
        entry = next((v for k, v in DISTRICTS.items() if k.lower() == district.lower()), None)
    if entry:
        return entry.get(lang, district)
    return district


# ── Premium features ───────────────────────────────────────────────────────────

FEATURES = {
    "speed":     {"price_stars": 100, "price_eur": 2},
    "hot":       {"price_stars": 50, "price_eur": 1},
    "history":   {"price_stars": 100, "price_eur": 2},
    "analytics": {"price_stars": 50, "price_eur": 1},
    "pro":       {"price_stars": 300, "price_eur": 5},
}

PRO_FEATURES = {"speed", "hot", "history", "analytics"}


# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class User:
    id: int
    username: Optional[str]
    first_name: Optional[str]
    language: str = 'en'
    alerts_paused: bool = False
    _active_features: set = field(default_factory=set)

    def has(self, feature: str) -> bool:
        if feature == "pro":
            return PRO_FEATURES.issubset(self._active_features)
        return feature in self._active_features

    @property
    def parse_interval_minutes(self) -> int:
        import os
        if self.has("speed"):
            return int(os.environ.get("PARSE_INTERVAL_PAID_MINUTES", 5))
        return int(os.environ.get("PARSE_INTERVAL_FREE_MINUTES", 30))


@dataclass
class Filter:
    id: str
    user_id: int
    city: str
    label: Optional[str] = None
    district: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    rooms_min: Optional[int] = None
    rooms_max: Optional[int] = None
    area_min: Optional[int] = None
    area_max: Optional[int] = None
    floor_min: Optional[int] = None
    floor_max: Optional[int] = None
    series: Optional[str] = None
    long_term_only: bool = True
    is_active: bool = True

    def display_name(self, lang: str) -> str:
        if self.label:
            return self.label
        parts = [city_name(self.city, lang)]
        if self.district:
            parts.append(self.district)
        if self.price_max:
            parts.append(f"≤{self.price_max}€")
        return ", ".join(parts)

    def full_summary(self, lang: str) -> str:
        from bot.i18n import t
        lines = []
        lines.append(f"🏙 {t('city', lang)}: {city_name(self.city, lang)}")
        if self.district:
            lines.append(f"📍 {t('district', lang)}: {district_name(self.district, lang)}")
        if self.price_min or self.price_max:
            lo = self.price_min or "—"
            hi = self.price_max or "—"
            lines.append(f"💶 {t('price', lang)}: {lo} – {hi} €")
        if self.rooms_min or self.rooms_max:
            lo = self.rooms_min or "—"
            hi = self.rooms_max or "—"
            lines.append(f"🚪 {t('rooms', lang)}: {lo} – {hi}")
        if self.area_min or self.area_max:
            lo = self.area_min or "—"
            hi = self.area_max or "—"
            lines.append(f"📐 {t('area', lang)}: {lo} – {hi} m²")
        if self.floor_min or self.floor_max:
            lo = self.floor_min or "—"
            hi = self.floor_max or "—"
            lines.append(f"🏢 {t('floor', lang)}: {lo} – {hi}")
        if self.series:
            lines.append(f"🏗 {t('series', lang)}: {series_name(self.series, lang)}")
        if self.long_term_only:
            lines.append(f"📅 {t('long_term_only', lang)}")
        return "\n".join(lines)


@dataclass
class Listing:
    id: str                          # 'sslv_12345678'
    source: str                      # 'sslv'
    url: str
    city: str
    title: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    price: Optional[int] = None
    rooms: Optional[int] = None
    area: Optional[int] = None
    floor: Optional[int] = None
    floor_total: Optional[int] = None
    series: Optional[str] = None
    is_long_term: Optional[bool] = None
    contacts: dict = field(default_factory=dict)
    image_urls: list = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class PricePoint:
    listing_id: str
    price: int
    recorded_at: datetime
