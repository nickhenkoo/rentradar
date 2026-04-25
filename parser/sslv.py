import re
import asyncio
import random
import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from parser.base import BaseParser
from parser.proxy import ProxyPool, fetch_with_proxy
from core.models import Listing

logger = logging.getLogger(__name__)

SS_LV_CITY_URLS = {
    "riga":       "https://www.ss.lv/lv/real-estate/flats/riga/all/hand_over/",
    "jurmala":    "https://www.ss.lv/lv/real-estate/flats/jurmala/all/hand_over/",
    "daugavpils": "https://www.ss.lv/lv/real-estate/flats/daugavpils-and-region/daugavpils/hand_over/",
    "liepaja":    "https://www.ss.lv/lv/real-estate/flats/liepaja-and-region/liepaja/hand_over/",
    "jelgava":    "https://www.ss.lv/lv/real-estate/flats/jelgava-and-region/jelgava/hand_over/",
    "ventspils":  "https://www.ss.lv/lv/real-estate/flats/ventspils/all/hand_over/",
    "rezekne":    "https://www.ss.lv/lv/real-estate/flats/rezekne-and-region/rezekne/hand_over/",
    "jekabpils":  "https://www.ss.lv/lv/real-estate/flats/jekabpils-and-region/jekabpils/hand_over/",
    "valmiera":   "https://www.ss.lv/lv/real-estate/flats/valmiera-and-region/valmiera/hand_over/",
    "ogre":       "https://www.ss.lv/lv/real-estate/flats/ogre-and-region/ogre/hand_over/",
}

# Short-term / daily rental keywords to detect non-long-term listings
SHORT_TERM_KEYWORDS = ("daily", "dienas", "посуточно", "nakts", "nightly", "€/day", "€/night")

_ua = UserAgent()


def _random_headers() -> dict:
    return {
        "User-Agent": _ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "lv-LV,lv;q=0.9,en;q=0.8,ru;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }


class SsLvParser(BaseParser):
    SOURCE = "sslv"

    def __init__(self, proxy_pool: ProxyPool):
        self._pool = proxy_pool

    async def fetch_listings(self) -> list[Listing]:
        """Fetch all cities concurrently with inter-request delays."""
        tasks = [self._fetch_city(city, url) for city, url in SS_LV_CITY_URLS.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        listings = []
        for city, result in zip(SS_LV_CITY_URLS.keys(), results):
            if isinstance(result, Exception):
                logger.warning("Failed to fetch %s: %s", city, result)
            else:
                listings.extend(result)
        return listings

    async def _fetch_city(self, city: str, url: str) -> list[Listing]:
        # Stagger requests to avoid hammering ss.lv
        await asyncio.sleep(random.uniform(1.0, 4.0))
        html = await fetch_with_proxy(url, self._pool)
        if not html:
            logger.warning("No HTML for city: %s", city)
            return []
        return self._parse(html, city)

    def _parse(self, html: str, city: str) -> list[Listing]:
        soup = BeautifulSoup(html, "lxml")
        listings = []

        for row in soup.select("tr[id^='tr_']"):
            try:
                listing_id = row.get("id", "").replace("tr_", "")
                if not listing_id:
                    continue

                link_tag = row.select_one("a.am")
                if not link_tag:
                    continue

                url = "https://www.ss.lv" + link_tag["href"]
                title = link_tag.get_text(strip=True)

                # Cells: [0]=checkbox [1]=image [2]=title [3]=district [4]=rooms
                #        [5]=area [6]=floor [7]=series [8]=price
                cells = row.select("td")

                price, is_long_term = self._extract_price_and_term(cells)

                # Skip short-term listings at parse level (title check)
                title_lower = title.lower()
                if any(kw in title_lower for kw in SHORT_TERM_KEYWORDS):
                    is_long_term = False

                district, street = self._extract_district_and_street(cells)
                listings.append(Listing(
                    id=f"sslv_{listing_id}",
                    source=self.SOURCE,
                    url=url,
                    city=city,
                    title=title,
                    district=district,
                    street=street,
                    price=price,
                    rooms=self._extract_rooms(cells),
                    area=self._extract_area(cells),
                    floor=self._extract_floor(cells),
                    floor_total=self._extract_floor_total(cells),
                    series=self._extract_series(cells),
                    is_long_term=is_long_term,
                    image_urls=self._extract_images(row),
                    contacts=self._extract_contact_url(row),
                ))
            except Exception:
                continue

        return listings

    # Keywords that indicate daily/nightly pricing in price cell text
    _SHORT_TERM_PRICE_KEYWORDS = ("day", "nakts", "dien", "nakt", "night", "час", "hour")

    def _extract_price_and_term(self, cells) -> tuple[Optional[int], Optional[bool]]:
        """
        Price cell (last) looks like '450 €/month', '40 €/day', '30 €/dien.'
        Returns (price_int_or_None, is_long_term_bool_or_None).
        """
        if not cells:
            return None, None
        price_text = cells[-1].get_text(strip=True)
        match = re.search(r'(\d[\d\s\xa0 ,.]*)\s*€', price_text)
        if not match:
            return None, None
        price = int(re.sub(r'[^\d]', '', match.group(1)))
        pt_lower = price_text.lower()
        is_long_term = not any(kw in pt_lower for kw in self._SHORT_TERM_PRICE_KEYWORDS)
        return price, is_long_term

    def _extract_rooms(self, cells) -> Optional[int]:
        # cells[4] = rooms
        if len(cells) > 4:
            text = cells[4].get_text(strip=True)
            if text.isdigit():
                val = int(text)
                if 1 <= val <= 20:
                    return val
        return None

    def _extract_area(self, cells) -> Optional[int]:
        # cells[5] = area (plain number, no unit in table)
        if len(cells) > 5:
            text = cells[5].get_text(strip=True)
            if text.isdigit():
                val = int(text)
                if 5 <= val <= 1000:
                    return val
        return None

    def _extract_floor(self, cells) -> Optional[int]:
        # cells[6] = floor, format '3/5' or '3'
        if len(cells) > 6:
            text = cells[6].get_text(strip=True)
            m = re.match(r'^(\d+)', text)
            if m:
                return int(m.group(1))
        return None

    def _extract_floor_total(self, cells) -> Optional[int]:
        if len(cells) > 6:
            text = cells[6].get_text(strip=True)
            m = re.search(r'/(\d+)', text)
            if m:
                return int(m.group(1))
        return None

    # Map ss.lv raw series labels → SERIES keys in core/models.py
    _SERIES_MAP = {
        # English labels
        "New": "new", "New pr.": "new", "New project": "new",
        "Pre-war": "prewar", "Pre-war house": "prewar", "Prewar": "prewar",
        "Chrusch.": "khrushchevka", "Khrushch.": "khrushchevka",
        "Stalin project": "stalinka", "Stalinka": "stalinka",
        "Czech pr.": "czech", "Czech project": "czech",
        "French pr.": "french", "French project": "french",
        "Lit pr.": "lithuanian_new", "Lith.new pr.": "lithuanian_new", "Lith.old pr.": "lithuanian_old",
        "Small f.": "small_family", "Sm.fam.": "small_family", "Small family": "small_family",
        "Spec.pr.": "special", "Special project": "special",
        "Wooden": "wooden", "Wooden house": "wooden",
        "Brick": "brick", "Brick house": "brick",
        "Brezhnevka": "brezhnevka",
        "103-th": "103", "104-th": "104", "119-th": "119", "467-th": "467", "602-th": "602",
        # Latvian labels (from /lv/ parsing)
        "Jaun.": "new", "Jaunbūve": "new",
        "P. kara": "prewar", "Pirmskar.": "prewar",
        "Hrušč.": "khrushchevka",
        "Staļina": "stalinka",
        "Čehu": "czech", "Čehu pr.": "czech",
        "Franču": "french", "Franču pr.": "french",
        "Lit.j.pr.": "lithuanian_new", "Lit.v.pr.": "lithuanian_old",
        "Mazģim.": "small_family",
        "Spec.pr.": "special",
        "Koka": "wooden", "Ķieģ.": "brick",
        "Brežņ.": "brezhnevka",
        "103.": "103", "104.": "104", "119.": "119", "467.": "467", "602.": "602",
        # Russian labels
        "Нов.": "new", "Дов. дом": "prewar", "Хрущ.": "khrushchevka",
        "Сталинка": "stalinka", "Чеш. пр.": "czech", "Лит. пр.": "lithuanian_new",
        "Фр. пр.": "french", "Брежн.": "brezhnevka",
        "119-я": "119", "602-я": "602",
    }

    def _extract_series(self, cells) -> Optional[str]:
        """Return SERIES key (for series_name() translation), or None."""
        if len(cells) > 7:
            text = cells[7].get_text(strip=True)
            if text:
                return self._SERIES_MAP.get(text, text)  # fallback to raw label if unmapped
        return None

    def _extract_district_and_street(self, cells) -> tuple[Optional[str], Optional[str]]:
        """cells[3]: first line = district, second line = street address."""
        if len(cells) > 3:
            parts = [p.strip() for p in cells[3].get_text(separator="\n", strip=True).split("\n") if p.strip()]
            district = parts[0] if parts else None
            street = parts[1] if len(parts) > 1 else None
            return district, street
        return None, None

    def _extract_contact_url(self, row) -> dict:
        """Extract ss.lv message form URL from listing row (/msg/... links)."""
        for a in row.select("a[href^='/msg/']"):
            href = a.get("href", "")
            if href:
                return {"contact_url": "https://www.ss.lv" + href}
        return {}

    def _extract_images(self, row) -> list[str]:
        """
        Collect all thumbnail images from the row and upgrade to 800px quality.
        Thumbnail pattern: .th2.jpg → replace with .800.jpg
        """
        images = []
        for img in row.select("img.isfoto, img.foto_list"):
            src = img.get("src", "")
            if src:
                # Upgrade thumbnail to full-size
                full = re.sub(r'\.th\d+\.jpg$', '.800.jpg', src)
                if full not in images:
                    images.append(full)
        return images

    async def fetch_detail_photos(self, listing_url: str) -> list[str]:
        """
        Fetch detail page and extract all photos (up to 10).
        Only called for new matched listings.
        """
        await asyncio.sleep(random.uniform(1.5, 3.5))
        html = await fetch_with_proxy(listing_url, self._pool)
        if not html:
            return []
        soup = BeautifulSoup(html, "lxml")
        images = []
        for img in soup.select("img"):
            src = img.get("src", "")
            if src and "gallery" in src and ".jpg" in src:
                full = re.sub(r'\.th\d+\.jpg$', '.800.jpg', src)
                if full not in images:
                    images.append(full)
            if len(images) >= 10:
                break
        return images

    async def fetch_contacts(self, listing_url: str) -> dict:
        """
        Fetch listing detail page and extract contacts.
        Called only for new listings that match at least one filter.
        Returns {phones: [...], emails: [...], name: ""}
        """
        await asyncio.sleep(random.uniform(2.0, 5.0))
        html = await fetch_with_proxy(listing_url, self._pool)
        if not html:
            return {}
        return self._parse_contacts(html)

    def _parse_contacts(self, html: str) -> dict:
        soup = BeautifulSoup(html, "lxml")
        contacts: dict = {"phones": [], "emails": [], "name": ""}

        # Phone numbers
        for el in soup.select(".phone_num, [class*='phone']"):
            text = el.get_text(strip=True)
            phones = re.findall(r'\+?[\d\s\-]{7,15}', text)
            for p in phones:
                p = p.strip()
                if p and p not in contacts["phones"]:
                    contacts["phones"].append(p)

        # Email addresses — skip SS.lv anonymous relay links (mailto:?body=...)
        for el in soup.select("a[href^='mailto:']"):
            href = el.get("href", "")
            email = href.replace("mailto:", "").strip()
            if "@" in email and email not in contacts["emails"]:
                # Real email address
                contacts["emails"].append(email)
            elif email.startswith("?body=") and "contact_url" not in contacts:
                # SS.lv relay: extract the ss.lv message URL from body param
                from urllib.parse import parse_qs, unquote
                try:
                    body = parse_qs(email.lstrip("?")).get("body", [""])[0]
                    msg_url = unquote(body).strip()
                    if msg_url.startswith("http"):
                        contacts["contact_url"] = msg_url
                except Exception:
                    pass

        # Owner/agent name
        name_el = soup.select_one(".user_name, [class*='author'], [class*='owner']")
        if name_el:
            contacts["name"] = name_el.get_text(strip=True)

        return contacts if (contacts["phones"] or contacts["emails"]) else {}
