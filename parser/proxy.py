import random
import logging
import httpx
import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

_WEBSHARE_API = "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=100"


class ProxyPool:
    """
    Webshare.io proxy pool via REST API.

    Reads PROXY_API_KEY from env (Authorization: Token <key>).
    Falls back to PROXY_LIST_URL download format if PROXY_API_KEY is not set.
    If neither is set — all requests go direct (no proxy).

    Proxy format from Webshare API:
      { "username": "...", "password": "...", "proxy_address": "...", "port": ... }
    → http://username:password@proxy_address:port
    """

    COOLDOWN_MINUTES = 5
    REFRESH_HOURS = 12

    def __init__(self):
        self._pool: dict[str, Optional[datetime]] = {}
        self._last_refresh: Optional[datetime] = None

    async def get(self) -> Optional[str]:
        await self._maybe_refresh()
        available = [
            p for p, cooldown_until in self._pool.items()
            if cooldown_until is None or datetime.now() > cooldown_until
        ]
        return random.choice(available) if available else None

    def mark_bad(self, proxy: str) -> None:
        self._pool[proxy] = datetime.now() + timedelta(minutes=self.COOLDOWN_MINUTES)

    async def _maybe_refresh(self) -> None:
        if (
            self._last_refresh is None
            or datetime.now() - self._last_refresh > timedelta(hours=self.REFRESH_HOURS)
        ):
            await self._refresh()

    async def _refresh(self) -> None:
        api_key = os.environ.get("PROXY_API_KEY", "").strip()
        list_url = os.environ.get("PROXY_LIST_URL", "").strip()

        if api_key:
            await self._refresh_from_api(api_key)
        elif list_url:
            await self._refresh_from_download(list_url)
        else:
            logger.warning("No PROXY_API_KEY or PROXY_LIST_URL set — running without proxies")

    async def _refresh_from_api(self, api_key: str) -> None:
        """Fetch proxy list via Webshare REST API (preferred method)."""
        headers = {"Authorization": f"Token {api_key}"}
        try:
            proxies: list[str] = []
            url = _WEBSHARE_API
            async with httpx.AsyncClient(timeout=15) as client:
                while url:
                    r = await client.get(url, headers=headers)
                    r.raise_for_status()
                    data = r.json()
                    for p in data.get("results", []):
                        proxy_url = (
                            f"http://{p['username']}:{p['password']}"
                            f"@{p['proxy_address']}:{p['port']}"
                        )
                        proxies.append(proxy_url)
                    url = data.get("next")  # follow pagination

            self._update_pool(set(proxies))
            logger.info("Webshare API: loaded %d proxies", len(proxies))
        except Exception as e:
            logger.warning("Webshare API refresh failed: %s", e)

    async def _refresh_from_download(self, list_url: str) -> None:
        """Fetch proxy list from a download URL (fallback)."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(list_url)
                r.raise_for_status()

            proxies: list[str] = []
            for line in r.text.strip().splitlines():
                line = line.strip()
                if line:
                    p = _parse_proxy_line(line)
                    if p:
                        proxies.append(p)

            self._update_pool(set(proxies))
            logger.info("Proxy download URL: loaded %d proxies", len(proxies))
        except Exception as e:
            logger.warning("Proxy download refresh failed: %s", e)

    def _update_pool(self, new_proxies: set[str]) -> None:
        for p in list(self._pool.keys()):
            if p not in new_proxies:
                del self._pool[p]
        for p in new_proxies:
            if p not in self._pool:
                self._pool[p] = None
        self._last_refresh = datetime.now()


def _parse_proxy_line(line: str) -> Optional[str]:
    """
    Parse a proxy list line into an httpx-compatible proxy URL.
      ip:port:username:password  →  http://username:password@ip:port
      username:password@ip:port  →  http://username:password@ip:port
      ip:port                    →  http://ip:port  (anonymous)
    """
    if "@" in line:
        return line if line.startswith("http") else f"http://{line}"
    parts = line.split(":")
    if len(parts) == 4:
        ip, port, username, password = parts
        return f"http://{username}:{password}@{ip}:{port}"
    if len(parts) == 2:
        return f"http://{line}"
    return None


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "lv-LV,lv;q=0.9,en;q=0.8,ru;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


async def fetch_with_proxy(
    url: str,
    pool: ProxyPool,
    retries: int = 3,
) -> Optional[str]:
    """
    Fetch URL through proxy pool. Returns HTML or None if all retries fail.
    Last retry attempts a direct connection if the pool is empty.
    """
    for attempt in range(retries):
        proxy = await pool.get()

        if proxy is None and attempt < retries - 1:
            logger.debug("No proxy available, attempt %d/%d — will retry", attempt + 1, retries)
            await asyncio.sleep(random.uniform(2.0, 4.0))
            continue

        await asyncio.sleep(random.uniform(1.0, 2.5))

        try:
            async with httpx.AsyncClient(
                proxy=proxy,
                timeout=20,
                follow_redirects=True,
            ) as client:
                r = await client.get(url, headers=_HEADERS)

            if r.status_code == 429:
                logger.debug("Rate-limited (attempt %d/%d, proxy %s)", attempt + 1, retries, proxy)
                if proxy:
                    pool.mark_bad(proxy)
                await asyncio.sleep(random.uniform(5.0, 10.0))
                continue

            if r.status_code == 200:
                return r.text

            logger.debug("HTTP %d on attempt %d — %s", r.status_code, attempt + 1, url)

        except (httpx.TimeoutException, httpx.ProxyError, httpx.ConnectError) as e:
            logger.debug("Proxy error attempt %d/%d: %s", attempt + 1, retries, e)
            if proxy:
                pool.mark_bad(proxy)

    logger.warning("All %d retries failed for %s", retries, url)
    return None
