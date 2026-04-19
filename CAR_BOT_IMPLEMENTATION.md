# CarRadar — Реализация бота для авто на базе RentRadar

> Пошаговое руководство по адаптации этого репо для мониторинга объявлений об автомобилях на ss.lv.
> Все новые файлы создаются рядом с существующими — структура репо не ломается.

---

## Обзор изменений

| Компонент | Действие | Объём |
|---|---|---|
| `core/models.py` | Добавить `CarListing`, `CarFilter`, `BRANDS`, `FUEL_TYPES`, `TRANSMISSION` | ~120 строк |
| `core/db.py` | Добавить CRUD для car-таблиц | ~80 строк |
| `core/matcher.py` | Добавить `car_matches()` | ~30 строк |
| `core/notifier.py` | Добавить `send_car_alert()` | ~40 строк |
| `parser/sslv_cars.py` | Новый парсер ss.lv/transport/cars | ~200 строк |
| `parser/runner.py` | Добавить car-цикл рядом с rent-циклом | ~30 строк |
| `bot/i18n.py` | Добавить ключи для авто в STRINGS | ~80 ключей |
| `bot/keyboards.py` | Добавить `brand_keyboard`, `fuel_keyboard`, `transmission_keyboard` | ~50 строк |
| `bot/handlers/car_filters.py` | Новый ConversationHandler для авто | ~250 строк |
| `bot/app.py` | Зарегистрировать car-хендлеры | ~10 строк |
| `supabase/` | Миграция 011: car_listings, car_filters | SQL |

---

## Шаг 1 — Модели (`core/models.py`)

Добавить в конец файла после существующих констант.

```python
# ── Car constants ──────────────────────────────────────────────────────────────

BRANDS: dict[str, dict] = {
    "any":        {"en": "Any brand",    "ru": "Любая марка",   "lv": "Jebkura marka"},
    "audi":       {"en": "Audi",         "ru": "Audi",          "lv": "Audi"},
    "bmw":        {"en": "BMW",          "ru": "BMW",           "lv": "BMW"},
    "ford":       {"en": "Ford",         "ru": "Ford",          "lv": "Ford"},
    "honda":      {"en": "Honda",        "ru": "Honda",         "lv": "Honda"},
    "hyundai":    {"en": "Hyundai",      "ru": "Hyundai",       "lv": "Hyundai"},
    "kia":        {"en": "Kia",          "ru": "Kia",           "lv": "Kia"},
    "mazda":      {"en": "Mazda",        "ru": "Mazda",         "lv": "Mazda"},
    "mercedes":   {"en": "Mercedes",     "ru": "Mercedes",      "lv": "Mercedes"},
    "mitsubishi": {"en": "Mitsubishi",   "ru": "Mitsubishi",    "lv": "Mitsubishi"},
    "nissan":     {"en": "Nissan",       "ru": "Nissan",        "lv": "Nissan"},
    "opel":       {"en": "Opel",         "ru": "Opel",          "lv": "Opel"},
    "renault":    {"en": "Renault",      "ru": "Renault",       "lv": "Renault"},
    "skoda":      {"en": "Škoda",        "ru": "Škoda",         "lv": "Škoda"},
    "toyota":     {"en": "Toyota",       "ru": "Toyota",        "lv": "Toyota"},
    "volkswagen": {"en": "Volkswagen",   "ru": "Volkswagen",    "lv": "Volkswagen"},
    "volvo":      {"en": "Volvo",        "ru": "Volvo",         "lv": "Volvo"},
    "other":      {"en": "Other",        "ru": "Другая",        "lv": "Cita"},
}

FUEL_TYPES: dict[str, dict] = {
    "petrol":   {"en": "Petrol",    "ru": "Бензин",   "lv": "Benzīns"},
    "diesel":   {"en": "Diesel",    "ru": "Дизель",   "lv": "Dīzelis"},
    "hybrid":   {"en": "Hybrid",    "ru": "Гибрид",   "lv": "Hibrīds"},
    "electric": {"en": "Electric",  "ru": "Электро",  "lv": "Elektro"},
    "gas":      {"en": "Gas (LPG)", "ru": "Газ (LPG)","lv": "Gāze (LPG)"},
}

TRANSMISSION: dict[str, dict] = {
    "manual":    {"en": "Manual",    "ru": "Механика",   "lv": "Manuāla"},
    "automatic": {"en": "Automatic", "ru": "Автомат",    "lv": "Automāts"},
}


def brand_name(key: str, lang: str) -> str:
    return BRANDS.get(key, {}).get(lang) or BRANDS.get(key, {}).get("en", key)

def fuel_name(key: str, lang: str) -> str:
    return FUEL_TYPES.get(key, {}).get(lang) or FUEL_TYPES.get(key, {}).get("en", key)

def transmission_name(key: str, lang: str) -> str:
    return TRANSMISSION.get(key, {}).get(lang) or TRANSMISSION.get(key, {}).get("en", key)


@dataclass
class CarListing:
    id: str                          # "sslv_cars_XXXXXXXX"
    source: str                      # "sslv_cars"
    url: str
    title: str
    brand: str | None = None         # ключ из BRANDS
    model: str | None = None         # свободный текст: "Passat", "A4", ...
    year: int | None = None
    price: int | None = None         # EUR
    mileage: int | None = None       # км
    engine_volume: float | None = None  # литры (1.6, 2.0, ...)
    fuel_type: str | None = None     # ключ из FUEL_TYPES
    transmission: str | None = None  # ключ из TRANSMISSION
    color: str | None = None
    city: str | None = None          # ключ из CITIES
    description: str | None = None
    image_urls: list[str] = field(default_factory=list)
    contacts: dict = field(default_factory=dict)
    last_seen: datetime | None = None


@dataclass
class CarFilter:
    id: int
    user_id: int
    brand: str | None = None          # None = любая
    model: str | None = None          # None = любая
    year_min: int | None = None
    year_max: int | None = None
    price_min: int | None = None
    price_max: int | None = None
    mileage_max: int | None = None
    engine_min: float | None = None
    engine_max: float | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    city: str | None = None           # None = вся Латвия
    label: str | None = None
    is_active: bool = True

    def display_name(self, lang: str) -> str:
        if self.label:
            return self.label
        parts = []
        if self.brand:
            parts.append(brand_name(self.brand, lang))
        if self.model:
            parts.append(self.model)
        if self.price_max:
            parts.append(f"≤{self.price_max}€")
        return ", ".join(parts) if parts else "Car filter"

    def full_summary(self, lang: str) -> str:
        lines = []
        if self.brand:
            lines.append(f"🚗 {brand_name(self.brand, lang)}" +
                         (f" {self.model}" if self.model else ""))
        if self.year_min or self.year_max:
            lo = self.year_min or "…"
            hi = self.year_max or "…"
            lines.append(f"📅 {lo} – {hi}")
        if self.price_min or self.price_max:
            lo = self.price_min or "…"
            hi = self.price_max or "…"
            lines.append(f"💶 {lo} – {hi} €")
        if self.mileage_max:
            lines.append(f"🛣 ≤ {self.mileage_max} km")
        if self.engine_min or self.engine_max:
            lo = self.engine_min or "…"
            hi = self.engine_max or "…"
            lines.append(f"⚙️ {lo} – {hi} L")
        if self.fuel_type:
            lines.append(f"⛽ {fuel_name(self.fuel_type, lang)}")
        if self.transmission:
            lines.append(f"🔧 {transmission_name(self.transmission, lang)}")
        if self.city:
            lines.append(f"🏙 {city_name(self.city, lang)}")
        return "\n".join(lines) if lines else "—"
```

---

## Шаг 2 — Парсер (`parser/sslv_cars.py`)

Новый файл, повторяет структуру `sslv.py`.

```python
"""ss.lv cars parser — /lv/transport/cars/"""
import asyncio
import re
import random
from bs4 import BeautifulSoup
from core.models import CarListing, BRANDS

SS_LV_CAR_URLS = {
    "riga":        "https://www.ss.lv/lv/transport/cars/riga/sell/",
    "all_latvia":  "https://www.ss.lv/lv/transport/cars/sell/",
}

# Маппинг Латвийских меток ss.lv → ключи BRANDS
_BRAND_MAP: dict[str, str] = {
    "audi": "audi", "bmw": "bmw", "ford": "ford", "honda": "honda",
    "hyundai": "hyundai", "kia": "kia", "mazda": "mazda",
    "mercedes-benz": "mercedes", "mercedes": "mercedes",
    "mitsubishi": "mitsubishi", "nissan": "nissan", "opel": "opel",
    "renault": "renault", "škoda": "skoda", "skoda": "skoda",
    "toyota": "toyota", "volkswagen": "volkswagen", "vw": "volkswagen",
    "volvo": "volvo",
}

_FUEL_MAP: dict[str, str] = {
    "benzīns": "petrol", "benzins": "petrol", "бензин": "petrol", "petrol": "petrol",
    "dīzelis": "diesel", "dizelis": "diesel", "дизель": "diesel", "diesel": "diesel",
    "hibrīds": "hybrid", "hibr": "hybrid", "гибрид": "hybrid",
    "elektro": "electric", "электро": "electric", "electric": "electric",
    "gāze": "gas", "gaze": "gas", "gas": "gas", "lpg": "gas",
}

_TRANS_MAP: dict[str, str] = {
    "manuāla": "manual", "manuala": "manual", "механика": "manual", "manual": "manual",
    "automāts": "automatic", "automats": "automatic", "автомат": "automatic", "auto": "automatic",
}


class SsLvCarsParser:
    def __init__(self, proxy_pool=None):
        self._proxy = proxy_pool

    async def fetch_listings(self) -> list[CarListing]:
        tasks = [self._fetch_section(key, url)
                 for key, url in SS_LV_CAR_URLS.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        listings = []
        seen = set()
        for r in results:
            if isinstance(r, Exception):
                continue
            for l in r:
                if l.id not in seen:
                    seen.add(l.id)
                    listings.append(l)
        return listings

    async def _fetch_section(self, section_key: str, url: str) -> list[CarListing]:
        await asyncio.sleep(random.uniform(1.0, 4.0))
        html = await self._proxy.get(url) if self._proxy else await self._plain_get(url)
        if not html:
            return []
        return self._parse(html, section_key)

    async def _plain_get(self, url: str) -> str | None:
        import httpx
        from fake_useragent import UserAgent
        headers = {
            "User-Agent": UserAgent().random,
            "Accept-Language": "lv-LV,lv;q=0.9",
            "Referer": "https://www.ss.lv/",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                r = await client.get(url, headers=headers)
                r.raise_for_status()
                return r.text
            except Exception:
                return None

    def _parse(self, html: str, section_key: str) -> list[CarListing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []
        for row in soup.select("tr[id^='tr_']"):
            try:
                listing = self._parse_row(row, section_key)
                if listing:
                    listings.append(listing)
            except Exception:
                continue
        return listings

    def _parse_row(self, row, section_key: str) -> CarListing | None:
        link_tag = row.select_one("a.am")
        if not link_tag:
            return None
        href = link_tag.get("href", "")
        if not href.startswith("/lv/transport/cars/"):
            return None
        url = f"https://www.ss.lv{href}"
        listing_id = re.search(r"/(\d+)\.html", href)
        if not listing_id:
            return None
        lid = f"sslv_cars_{listing_id.group(1)}"
        title = link_tag.get_text(strip=True)

        cells = row.select("td")
        if len(cells) < 7:
            return None

        # Колонки ss.lv /transport/cars/
        # [0] checkbox, [1] image, [2] title/link, [3] year, [4] engine+fuel,
        # [5] mileage, [6] transmission, [-1] price
        year       = self._extract_year(cells)
        engine, fuel = self._extract_engine_fuel(cells)
        mileage    = self._extract_mileage(cells)
        trans      = self._extract_transmission(cells)
        price      = self._extract_price(cells)
        brand, model = self._extract_brand_model(title)
        images     = self._extract_images(row)

        return CarListing(
            id=lid,
            source="sslv_cars",
            url=url,
            title=title,
            brand=brand,
            model=model,
            year=year,
            price=price,
            mileage=mileage,
            engine_volume=engine,
            fuel_type=fuel,
            transmission=trans,
            image_urls=images,
        )

    def _extract_year(self, cells) -> int | None:
        try:
            text = cells[3].get_text(strip=True)
            m = re.search(r"(19|20)\d{2}", text)
            return int(m.group(0)) if m else None
        except Exception:
            return None

    def _extract_engine_fuel(self, cells) -> tuple[float | None, str | None]:
        try:
            text = cells[4].get_text(" ", strip=True).lower()
            engine = None
            fuel = None
            m = re.search(r"(\d+[.,]\d+)", text)
            if m:
                engine = float(m.group(1).replace(",", "."))
            for raw, key in _FUEL_MAP.items():
                if raw in text:
                    fuel = key
                    break
            return engine, fuel
        except Exception:
            return None, None

    def _extract_mileage(self, cells) -> int | None:
        try:
            text = cells[5].get_text(strip=True).replace(" ", "").replace("\xa0", "")
            m = re.search(r"(\d+)", text)
            v = int(m.group(1)) if m else None
            return v if v and v < 1_500_000 else None
        except Exception:
            return None

    def _extract_transmission(self, cells) -> str | None:
        try:
            text = cells[6].get_text(strip=True).lower()
            for raw, key in _TRANS_MAP.items():
                if raw in text:
                    return key
            return None
        except Exception:
            return None

    def _extract_price(self, cells) -> int | None:
        try:
            text = cells[-1].get_text(strip=True)
            m = re.search(r"(\d[\d\s]*)\s*€", text)
            if m:
                return int(re.sub(r"\s", "", m.group(1)))
            return None
        except Exception:
            return None

    def _extract_brand_model(self, title: str) -> tuple[str | None, str | None]:
        title_low = title.lower()
        for raw, key in _BRAND_MAP.items():
            if raw in title_low:
                rest = re.sub(re.escape(raw), "", title_low, flags=re.IGNORECASE).strip()
                model = rest.split()[0].capitalize() if rest.split() else None
                return key, model
        return None, title.split()[0] if title else None

    def _extract_images(self, row) -> list[str]:
        imgs = []
        for img in row.select("img.isfoto, img.foto_list"):
            src = img.get("src", "")
            if src:
                src = re.sub(r"\.th2\.jpg$", ".800.jpg", src)
                if src not in imgs:
                    imgs.append(src)
        return imgs
```

---

## Шаг 3 — Матчер (`core/matcher.py`)

Добавить в конец существующего файла:

```python
from core.models import CarListing, CarFilter  # добавить в импорты вверху файла


def car_matches(listing: CarListing, f: CarFilter) -> bool:
    """Returns True if CarListing satisfies all criteria in CarFilter."""
    if f.city and listing.city != f.city:
        return False
    if f.brand and listing.brand != f.brand:
        return False
    if f.model and listing.model and f.model.lower() not in listing.model.lower():
        return False
    if f.year_min and listing.year and listing.year < f.year_min:
        return False
    if f.year_max and listing.year and listing.year > f.year_max:
        return False
    if f.price_min and listing.price and listing.price < f.price_min:
        return False
    if f.price_max and listing.price and listing.price > f.price_max:
        return False
    if f.mileage_max and listing.mileage and listing.mileage > f.mileage_max:
        return False
    if f.engine_min and listing.engine_volume and listing.engine_volume < f.engine_min:
        return False
    if f.engine_max and listing.engine_volume and listing.engine_volume > f.engine_max:
        return False
    if f.fuel_type and listing.fuel_type and listing.fuel_type != f.fuel_type:
        return False
    if f.transmission and listing.transmission and listing.transmission != f.transmission:
        return False
    return True


def find_matching_car_filters(listing: CarListing, all_filters: list[CarFilter]) -> list[CarFilter]:
    return [f for f in all_filters if f.is_active and car_matches(listing, f)]
```

---

## Шаг 4 — База данных (`core/db.py`)

Добавить в конец существующего файла:

```python
# ── Car listings ───────────────────────────────────────────────────────────────

async def save_car_listing(listing: CarListing) -> bool:
    """Returns True if listing is new."""
    client = get_client()
    existing = await _retry(lambda: client.table("car_listings")
                            .select("id").eq("id", listing.id).execute())
    if existing.data:
        await _retry(lambda: client.table("car_listings")
                     .update({"last_seen": datetime.utcnow().isoformat()})
                     .eq("id", listing.id).execute())
        return False
    row = {
        "id": listing.id, "source": listing.source, "url": listing.url,
        "title": listing.title, "brand": listing.brand, "model": listing.model,
        "year": listing.year, "price": listing.price, "mileage": listing.mileage,
        "engine_volume": listing.engine_volume, "fuel_type": listing.fuel_type,
        "transmission": listing.transmission, "city": listing.city,
        "image_urls": listing.image_urls,
        "last_seen": datetime.utcnow().isoformat(),
    }
    try:
        await _retry(lambda: client.table("car_listings").insert(row).execute())
        return True
    except Exception:
        return False


async def get_all_active_car_filters() -> list["CarFilter"]:
    from core.models import CarFilter
    client = get_client()
    result = await _retry(lambda: client.table("car_filters")
                          .select("*").eq("is_active", True).execute())
    return [_row_to_car_filter(r) for r in (result.data or [])]


async def create_car_filter(user_id: int, **kwargs) -> "CarFilter":
    from core.models import CarFilter
    client = get_client()
    row = {"user_id": user_id, **kwargs}
    result = await _retry(lambda: client.table("car_filters").insert(row).execute())
    return _row_to_car_filter(result.data[0])


async def get_user_car_filters(user_id: int) -> list["CarFilter"]:
    from core.models import CarFilter
    client = get_client()
    result = await _retry(lambda: client.table("car_filters")
                          .select("*").eq("user_id", user_id).execute())
    return [_row_to_car_filter(r) for r in (result.data or [])]


async def delete_car_filter(filter_id: int, user_id: int) -> None:
    client = get_client()
    await _retry(lambda: client.table("car_filters")
                 .delete().eq("id", filter_id).eq("user_id", user_id).execute())


async def has_car_alert_been_sent(user_id: int, listing_id: str) -> bool:
    client = get_client()
    result = await _retry(lambda: client.table("sent_car_alerts")
                          .select("user_id").eq("user_id", user_id)
                          .eq("listing_id", listing_id).execute())
    return bool(result.data)


async def mark_car_alert_sent(user_id: int, listing_id: str) -> None:
    client = get_client()
    await _retry(lambda: client.table("sent_car_alerts")
                 .insert({"user_id": user_id, "listing_id": listing_id}).execute())


def _row_to_car_filter(row: dict) -> "CarFilter":
    from core.models import CarFilter
    return CarFilter(
        id=row["id"], user_id=row["user_id"],
        brand=row.get("brand"), model=row.get("model"),
        year_min=row.get("year_min"), year_max=row.get("year_max"),
        price_min=row.get("price_min"), price_max=row.get("price_max"),
        mileage_max=row.get("mileage_max"),
        engine_min=row.get("engine_min"), engine_max=row.get("engine_max"),
        fuel_type=row.get("fuel_type"), transmission=row.get("transmission"),
        city=row.get("city"), label=row.get("label"),
        is_active=row.get("is_active", True),
    )
```

---

## Шаг 5 — Нотифаер (`core/notifier.py`)

Добавить новую функцию рядом с `send_alert`:

```python
async def send_car_alert(bot, user, listing: CarListing, f: CarFilter) -> None:
    lang = user.language
    lines = [
        f"🚗 <b>{listing.title or 'Новое объявление'}</b>",
    ]
    if listing.price:
        lines.append(f"💶 <b>{listing.price} €</b>")
    details = []
    if listing.year:
        details.append(str(listing.year))
    if listing.engine_volume:
        details.append(f"{listing.engine_volume}L")
    if listing.fuel_type:
        details.append(fuel_name(listing.fuel_type, lang))
    if listing.transmission:
        details.append(transmission_name(listing.transmission, lang))
    if details:
        lines.append("⚙️ " + " · ".join(details))
    if listing.mileage:
        lines.append(f"🛣 {listing.mileage:,} km")
    lines.append("")
    lines.append(f"⚡ <i>{t('alert_matched_filter', lang, name=f.display_name(lang))}</i>")
    lines.append("")
    lines.append(t("alert_filter_summary", lang))
    lines.append(f.full_summary(lang))

    text = "\n".join(lines)
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_view", lang), url=listing.url),
    ]])

    if listing.image_urls:
        photo = await _fetch_image(listing.image_urls[0])
        if photo:
            try:
                await bot.send_photo(chat_id=user.id, photo=photo,
                                     caption=text, parse_mode="HTML",
                                     reply_markup=keyboard)
                return
            except Exception:
                pass
    await bot.send_message(chat_id=user.id, text=text,
                           parse_mode="HTML", reply_markup=keyboard)
```

---

## Шаг 6 — Runner (`parser/runner.py`)

Добавить car-цикл рядом с `run_parse_cycle`:

```python
async def run_car_parse_cycle(bot, user_tier: str = "free") -> None:
    """Parse ss.lv cars and send alerts. user_tier: 'paid' | 'free'"""
    from parser.sslv_cars import SsLvCarsParser
    from core.matcher import find_matching_car_filters
    from core.notifier import send_car_alert
    import core.db as db

    proxy = _get_proxy_pool()  # переиспользуем существующую функцию
    parser = SsLvCarsParser(proxy_pool=proxy)

    try:
        listings = await parser.fetch_listings()
    except Exception as e:
        logger.warning(f"Car parse failed: {e}")
        return

    all_filters = await db.get_all_active_car_filters()
    if not all_filters:
        return

    for listing in listings:
        is_new = await db.save_car_listing(listing)
        if not is_new:
            continue

        matching = find_matching_car_filters(listing, all_filters)
        if not matching:
            continue

        user_ids = {f.user_id for f in matching}
        for uid in user_ids:
            user = await db.get_user(uid)
            if not user or user.alerts_paused:
                continue
            if await db.has_car_alert_been_sent(uid, listing.id):
                continue
            user_filters = [f for f in matching if f.user_id == uid]
            try:
                await send_car_alert(bot, user, listing, user_filters[0])
                await db.mark_car_alert_sent(uid, listing.id)
            except Exception as e:
                logger.warning(f"Car alert send failed uid={uid}: {e}")
```

---

## Шаг 7 — Клавиатуры (`bot/keyboards.py`)

Добавить три новые функции:

```python
def brand_keyboard(lang: str) -> InlineKeyboardMarkup:
    from core.models import BRANDS
    buttons = []
    brand_keys = [k for k in BRANDS if k != "any"]
    for i in range(0, len(brand_keys), 2):
        row = []
        for key in brand_keys[i:i+2]:
            row.append(InlineKeyboardButton(
                BRANDS[key].get(lang, BRANDS[key]["en"]),
                callback_data=f"carbrand_{key}"
            ))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(
        BRANDS["any"].get(lang, "Any brand"), callback_data="carbrand_any"
    )])
    return InlineKeyboardMarkup(buttons)


def fuel_keyboard(lang: str) -> InlineKeyboardMarkup:
    from core.models import FUEL_TYPES
    buttons = []
    for key, names in FUEL_TYPES.items():
        buttons.append([InlineKeyboardButton(
            names.get(lang, names["en"]), callback_data=f"carfuel_{key}"
        )])
    buttons.append([InlineKeyboardButton(t("btn_any", lang), callback_data="carfuel_any")])
    return InlineKeyboardMarkup(buttons)


def transmission_keyboard(lang: str) -> InlineKeyboardMarkup:
    from core.models import TRANSMISSION
    buttons = [
        [InlineKeyboardButton(TRANSMISSION["manual"].get(lang, "Manual"),
                              callback_data="cartrans_manual"),
         InlineKeyboardButton(TRANSMISSION["automatic"].get(lang, "Automatic"),
                              callback_data="cartrans_automatic")],
        [InlineKeyboardButton(t("btn_any", lang), callback_data="cartrans_any")],
    ]
    return InlineKeyboardMarkup(buttons)
```

---

## Шаг 8 — i18n (`bot/i18n.py`)

Добавить в словарь `STRINGS` для каждого языка (`en`, `ru`, `lv`):

```python
# Английский (en):
"car_ask_brand":       "🚗 Choose a car brand:",
"car_ask_model":       "✏️ Enter the model name (e.g. Passat, A4) or tap Skip:",
"car_ask_year":        "📅 Enter year range (e.g. 2015-2022) or tap Skip:",
"car_ask_price":       "💶 Enter price range in € (e.g. 3000-12000) or tap Skip:",
"car_ask_mileage":     "🛣 Enter maximum mileage in km (e.g. 150000) or tap Skip:",
"car_ask_engine":      "⚙️ Enter engine volume range in litres (e.g. 1.6-2.0) or tap Skip:",
"car_ask_fuel":        "⛽ Choose fuel type:",
"car_ask_transmission":"🔧 Choose transmission:",
"car_ask_city":        "🏙 Choose a city or leave blank for all Latvia:",
"car_ask_label":       "🏷 Give this filter a name (optional) or tap Skip:",
"car_filter_saved":    "✅ Car filter saved! You'll get alerts for new listings.",
"car_filter_preview":  "🔍 Your car filter:",
"car_no_filters":      "You have no car filters. Use /addcarfilter to create one.",
"car_filter_deleted":  "🗑 Car filter deleted.",

# Русский (ru):
"car_ask_brand":       "🚗 Выберите марку автомобиля:",
"car_ask_model":       "✏️ Введите модель (например Passat, A4) или нажмите Пропустить:",
"car_ask_year":        "📅 Введите диапазон года (например 2015-2022) или Пропустить:",
"car_ask_price":       "💶 Введите диапазон цены в € (например 3000-12000) или Пропустить:",
"car_ask_mileage":     "🛣 Введите максимальный пробег в км (например 150000) или Пропустить:",
"car_ask_engine":      "⚙️ Введите объём двигателя в литрах (например 1.6-2.0) или Пропустить:",
"car_ask_fuel":        "⛽ Выберите тип топлива:",
"car_ask_transmission":"🔧 Выберите тип КПП:",
"car_ask_city":        "🏙 Выберите город или оставьте — вся Латвия:",
"car_ask_label":       "🏷 Дайте фильтру название (необязательно) или Пропустить:",
"car_filter_saved":    "✅ Фильтр на авто сохранён! Будем присылать новые объявления.",
"car_filter_preview":  "🔍 Ваш фильтр на авто:",
"car_no_filters":      "У вас нет фильтров на авто. Используйте /addcarfilter.",
"car_filter_deleted":  "🗑 Фильтр удалён.",

# Латышский (lv):
"car_ask_brand":       "🚗 Izvēlieties automašīnas marku:",
"car_ask_model":       "✏️ Ievadiet modeli (piem. Passat, A4) vai nospiediet Izlaist:",
"car_ask_year":        "📅 Ievadiet gadu diapazonu (piem. 2015-2022) vai Izlaist:",
"car_ask_price":       "💶 Ievadiet cenas diapazonu € (piem. 3000-12000) vai Izlaist:",
"car_ask_mileage":     "🛣 Ievadiet maksimālo nobraukumu km (piem. 150000) vai Izlaist:",
"car_ask_engine":      "⚙️ Ievadiet dzinēja tilpumu litros (piem. 1.6-2.0) vai Izlaist:",
"car_ask_fuel":        "⛽ Izvēlieties degvielas veidu:",
"car_ask_transmission":"🔧 Izvēlieties ātrumkārbu:",
"car_ask_city":        "🏙 Izvēlieties pilsētu vai atstājiet — visa Latvija:",
"car_ask_label":       "🏷 Piešķiriet filtram nosaukumu (nav obligāti) vai Izlaist:",
"car_filter_saved":    "✅ Automašīnu filtrs saglabāts!",
"car_filter_preview":  "🔍 Jūsu automašīnu filtrs:",
"car_no_filters":      "Nav automašīnu filtru. Izmantojiet /addcarfilter.",
"car_filter_deleted":  "🗑 Filtrs dzēsts.",
```

---

## Шаг 9 — ConversationHandler (`bot/handlers/car_filters.py`)

Новый файл — полный сценарий создания фильтра:

```python
"""Car filter creation ConversationHandler."""
import re
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters,
)
from bot.i18n import t
from bot.keyboards import (
    brand_keyboard, fuel_keyboard, transmission_keyboard,
    city_keyboard, skip_keyboard, confirm_keyboard, yes_no_keyboard,
)
import core.db as db
from core.models import CarFilter

(BRAND, MODEL, YEAR, PRICE, MILEAGE, ENGINE, FUEL,
 TRANSMISSION, CITY, LABEL, CONFIRM) = range(11)


def _lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", "en")


def _parse_range(text: str) -> tuple[float | None, float | None]:
    text = text.strip()
    m = re.match(r"^(\d+(?:[.,]\d+)?)\s*[-–]\s*(\d+(?:[.,]\d+)?)$", text)
    if m:
        lo = float(m.group(1).replace(",", "."))
        hi = float(m.group(2).replace(",", "."))
        return (lo, hi) if lo <= hi else (hi, lo)
    m2 = re.match(r"^(\d+(?:[.,]\d+)?)$", text)
    if m2:
        v = float(m2.group(1).replace(",", "."))
        return None, v
    return None, None


async def addcarfilter_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    user = await db.get_user(update.effective_user.id)
    lang = user.language if user else "en"
    context.user_data["lang"] = lang
    await update.message.reply_text(
        t("car_ask_brand", lang), reply_markup=brand_keyboard(lang)
    )
    return BRAND


async def brand_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    key = query.data.replace("carbrand_", "")
    context.user_data["brand"] = None if key == "any" else key
    await query.edit_message_text(
        t("car_ask_model", lang), reply_markup=skip_keyboard(lang)
    )
    return MODEL


async def model_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(context)
    context.user_data["model"] = update.message.text.strip()
    await update.message.reply_text(t("car_ask_year", lang), reply_markup=skip_keyboard(lang))
    return YEAR


async def model_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    context.user_data["model"] = None
    await query.edit_message_text(t("car_ask_year", lang), reply_markup=skip_keyboard(lang))
    return YEAR


async def year_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(context)
    lo, hi = _parse_range(update.message.text)
    if lo is not None or hi is not None:
        context.user_data["year_min"] = int(lo) if lo else None
        context.user_data["year_max"] = int(hi) if hi else None
    await update.message.reply_text(t("car_ask_price", lang), reply_markup=skip_keyboard(lang))
    return PRICE


async def year_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    context.user_data["year_min"] = None
    context.user_data["year_max"] = None
    await query.edit_message_text(t("car_ask_price", lang), reply_markup=skip_keyboard(lang))
    return PRICE


async def price_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(context)
    lo, hi = _parse_range(update.message.text)
    context.user_data["price_min"] = int(lo) if lo else None
    context.user_data["price_max"] = int(hi) if hi else None
    await update.message.reply_text(t("car_ask_mileage", lang), reply_markup=skip_keyboard(lang))
    return MILEAGE


async def price_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    context.user_data["price_min"] = None
    context.user_data["price_max"] = None
    await query.edit_message_text(t("car_ask_mileage", lang), reply_markup=skip_keyboard(lang))
    return MILEAGE


async def mileage_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(context)
    _, hi = _parse_range(update.message.text)
    context.user_data["mileage_max"] = int(hi) if hi else None
    await update.message.reply_text(t("car_ask_engine", lang), reply_markup=skip_keyboard(lang))
    return ENGINE


async def mileage_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    context.user_data["mileage_max"] = None
    await query.edit_message_text(t("car_ask_engine", lang), reply_markup=skip_keyboard(lang))
    return ENGINE


async def engine_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(context)
    lo, hi = _parse_range(update.message.text)
    context.user_data["engine_min"] = lo
    context.user_data["engine_max"] = hi
    await update.message.reply_text(t("car_ask_fuel", lang), reply_markup=fuel_keyboard(lang))
    return FUEL


async def engine_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    context.user_data["engine_min"] = None
    context.user_data["engine_max"] = None
    await query.edit_message_text(t("car_ask_fuel", lang), reply_markup=fuel_keyboard(lang))
    return FUEL


async def fuel_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    key = query.data.replace("carfuel_", "")
    context.user_data["fuel_type"] = None if key == "any" else key
    await query.edit_message_text(
        t("car_ask_transmission", lang), reply_markup=transmission_keyboard(lang)
    )
    return TRANSMISSION


async def transmission_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    key = query.data.replace("cartrans_", "")
    context.user_data["transmission"] = None if key == "any" else key
    await query.edit_message_text(
        t("car_ask_city", lang), reply_markup=city_keyboard(lang)
    )
    return CITY


async def city_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    key = query.data.replace("city_", "")
    context.user_data["city"] = None if key == "any" else key
    await query.edit_message_text(t("car_ask_label", lang), reply_markup=skip_keyboard(lang))
    return LABEL


async def label_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(context)
    context.user_data["label"] = update.message.text.strip()[:50]
    return await _show_preview(update, context)


async def label_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["label"] = None
    return await _show_preview(update, context)


async def _show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(context)
    d = context.user_data
    preview = CarFilter(
        id=0, user_id=0,
        brand=d.get("brand"), model=d.get("model"),
        year_min=d.get("year_min"), year_max=d.get("year_max"),
        price_min=d.get("price_min"), price_max=d.get("price_max"),
        mileage_max=d.get("mileage_max"),
        engine_min=d.get("engine_min"), engine_max=d.get("engine_max"),
        fuel_type=d.get("fuel_type"), transmission=d.get("transmission"),
        city=d.get("city"), label=d.get("label"),
    )
    text = f"{t('car_filter_preview', lang)}\n\n{preview.full_summary(lang)}"
    msg = update.callback_query or update.message
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=confirm_keyboard(lang)
        )
    else:
        await update.message.reply_text(text, reply_markup=confirm_keyboard(lang))
    return CONFIRM


async def confirm_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _lang(context)
    d = context.user_data
    await db.create_car_filter(
        user_id=query.from_user.id,
        brand=d.get("brand"), model=d.get("model"),
        year_min=d.get("year_min"), year_max=d.get("year_max"),
        price_min=d.get("price_min"), price_max=d.get("price_max"),
        mileage_max=d.get("mileage_max"),
        engine_min=d.get("engine_min"), engine_max=d.get("engine_max"),
        fuel_type=d.get("fuel_type"), transmission=d.get("transmission"),
        city=d.get("city"), label=d.get("label"),
    )
    await query.edit_message_text(t("car_filter_saved", lang))
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_car_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _lang(context)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(t("filter_cancelled", lang))
    else:
        await update.message.reply_text(t("filter_cancelled", lang))
    context.user_data.clear()
    return ConversationHandler.END


async def my_car_filters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await db.get_user(update.effective_user.id)
    lang = user.language if user else "en"
    car_filters = await db.get_user_car_filters(update.effective_user.id)
    if not car_filters:
        await update.message.reply_text(t("car_no_filters", lang))
        return
    for f in car_filters:
        text = f"<b>{f.display_name(lang)}</b>\n{f.full_summary(lang)}"
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(t("btn_delete", lang),
                                 callback_data=f"carfilter_delete_{f.id}")
        ]])
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)


async def delete_car_filter_callback(update: Update,
                                     context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = await db.get_user(query.from_user.id)
    lang = user.language if user else "en"
    filter_id = int(query.data.split("_")[-1])
    await db.delete_car_filter(filter_id, query.from_user.id)
    await query.edit_message_text(t("car_filter_deleted", lang))


def build_car_filter_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("addcarfilter", addcarfilter_start)],
        states={
            BRAND:        [CallbackQueryHandler(brand_chosen, pattern="^carbrand_")],
            MODEL:        [MessageHandler(filters.TEXT & ~filters.COMMAND, model_text),
                           CallbackQueryHandler(model_skip, pattern="^skip$")],
            YEAR:         [MessageHandler(filters.TEXT & ~filters.COMMAND, year_text),
                           CallbackQueryHandler(year_skip, pattern="^skip$")],
            PRICE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, price_text),
                           CallbackQueryHandler(price_skip, pattern="^skip$")],
            MILEAGE:      [MessageHandler(filters.TEXT & ~filters.COMMAND, mileage_text),
                           CallbackQueryHandler(mileage_skip, pattern="^skip$")],
            ENGINE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, engine_text),
                           CallbackQueryHandler(engine_skip, pattern="^skip$")],
            FUEL:         [CallbackQueryHandler(fuel_chosen, pattern="^carfuel_")],
            TRANSMISSION: [CallbackQueryHandler(transmission_chosen, pattern="^cartrans_")],
            CITY:         [CallbackQueryHandler(city_chosen, pattern="^city_")],
            LABEL:        [MessageHandler(filters.TEXT & ~filters.COMMAND, label_text),
                           CallbackQueryHandler(label_skip, pattern="^skip$")],
            CONFIRM:      [CallbackQueryHandler(confirm_save, pattern="^confirm$"),
                           CallbackQueryHandler(cancel_car_filter, pattern="^cancel$")],
        },
        fallbacks=[CommandHandler("cancel", cancel_car_filter)],
        per_message=False,
    )
```

---

## Шаг 10 — Регистрация хендлеров (`bot/app.py`)

```python
# Добавить в функцию сборки Application (рядом с другими хендлерами):
from bot.handlers.car_filters import (
    build_car_filter_handler, my_car_filters, delete_car_filter_callback
)

app.add_handler(build_car_filter_handler())
app.add_handler(CommandHandler("mycarfilters", my_car_filters))
app.add_handler(CallbackQueryHandler(delete_car_filter_callback,
                                      pattern="^carfilter_delete_"))
```

---

## Шаг 11 — Планировщик (`core/scheduler.py`)

Добавить car-job рядом с `parse_paid`/`parse_free`:

```python
scheduler.add_job(
    run_car_parse_cycle,
    trigger="interval",
    minutes=int(os.getenv("PARSE_INTERVAL_FREE_MINUTES", 30)),
    id="parse_cars",
    max_instances=1,
    coalesce=True,
    kwargs={"bot": application.bot, "user_tier": "free"},
)
```

---

## Шаг 12 — Миграция Supabase (`supabase/011_car_tables.sql`)

```sql
-- Car listings
CREATE TABLE IF NOT EXISTS car_listings (
    id              TEXT PRIMARY KEY,
    source          TEXT NOT NULL DEFAULT 'sslv_cars',
    url             TEXT NOT NULL,
    title           TEXT,
    brand           TEXT,
    model           TEXT,
    year            INTEGER,
    price           INTEGER,
    mileage         INTEGER,
    engine_volume   NUMERIC(4,1),
    fuel_type       TEXT,
    transmission    TEXT,
    city            TEXT,
    image_urls      TEXT[]  DEFAULT '{}',
    description     TEXT,
    last_seen       TIMESTAMPTZ DEFAULT now(),
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Car filters
CREATE TABLE IF NOT EXISTS car_filters (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    brand           TEXT,
    model           TEXT,
    year_min        INTEGER,
    year_max        INTEGER,
    price_min       INTEGER,
    price_max       INTEGER,
    mileage_max     INTEGER,
    engine_min      NUMERIC(4,1),
    engine_max      NUMERIC(4,1),
    fuel_type       TEXT,
    transmission    TEXT,
    city            TEXT,
    label           TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Dedup table
CREATE TABLE IF NOT EXISTS sent_car_alerts (
    user_id         BIGINT NOT NULL,
    listing_id      TEXT NOT NULL,
    sent_at         TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, listing_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_car_filters_user ON car_filters(user_id);
CREATE INDEX IF NOT EXISTS idx_car_filters_active ON car_filters(is_active);
CREATE INDEX IF NOT EXISTS idx_car_listings_last_seen ON car_listings(last_seen);
```

---

## Порядок выполнения

```
1. Добавить модели → core/models.py
2. Создать parser/sslv_cars.py
3. Дописать core/matcher.py
4. Дописать core/db.py
5. Дописать core/notifier.py
6. Дописать parser/runner.py
7. Дописать bot/keyboards.py
8. Дописать bot/i18n.py
9. Создать bot/handlers/car_filters.py
10. Дописать bot/app.py
11. Дописать core/scheduler.py
12. Применить SQL-миграцию через Supabase MCP
```

---

## Важные замечания

- **Колонки парсера** — нужно проверить реальный HTML ss.lv `/lv/transport/cars/` вручную, так как индексы cells[] могут отличаться от жилья. Открыть страницу → DevTools → найти `tr[id^='tr_']`.
- **BRAND_MAP** неполный — добавить все марки, которые встречаются на ss.lv.
- **Один бот, два домена** — `/addfilter` для жилья, `/addcarfilter` для авто. Пользователь выбирает сам.
- **Монетизация** — переиспользуется та же таблица `subscriptions`, те же FEATURES. Premium-скорость (5 мин) будет работать автоматически, если добавить car-цикл в `parse_paid`.
