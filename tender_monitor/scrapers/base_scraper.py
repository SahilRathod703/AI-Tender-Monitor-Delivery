"""
scrapers/base_scraper.py — Abstract base class for all portal scrapers.
Provides shared HTTP session, retry logic, and data model.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class RawTender:
    """Represents a single tender scraped from a portal."""
    title: str
    organization: str
    portal_source: str          # e.g., "CPPP", "GeM", "TN eProcurement"
    govt_type: str              # "Central" or "State"
    state: Optional[str]        # State name for state tenders; None for central
    url: str
    publish_date: Optional[date] = None
    deadline: Optional[date] = None
    tender_value: Optional[str] = None
    tender_id: Optional[str] = None
    raw_description: Optional[str] = None
    category: Optional[str] = None
    # Populated by summarizer later
    ai_summary: Optional[str] = None
    matched_keywords: list = field(default_factory=list)

    def unique_key(self) -> str:
        """Deterministic key for deduplication."""
        return f"{self.portal_source}:{self.tender_id or self.url}"


class BaseScraper(ABC):
    """Base class all scrapers inherit from."""

    name: str = "BaseScraper"
    base_url: str = ""

    def __init__(self, settings):
        self.settings = settings
        self.session: Optional[aiohttp.ClientSession] = None

    # ── HTTP Helpers ───────────────────────────────────────────────────────

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.settings.REQUEST_TIMEOUT)
            headers = {"User-Agent": self.settings.USER_AGENT}
            self.session = aiohttp.ClientSession(
                timeout=timeout, headers=headers
            )
        return self.session

    async def _fetch(self, url: str, params: dict = None) -> Optional[str]:
        """GET a URL with automatic retries on failure."""
        session = await self._get_session()

        for attempt in range(1, self.settings.MAX_RETRIES + 1):
            try:
                async with session.get(url, params=params, ssl=False) as resp:
                    if resp.status == 200:
                        return await resp.text(errors="replace")
                    logger.warning(
                        f"[{self.name}] HTTP {resp.status} for {url} "
                        f"(attempt {attempt}/{self.settings.MAX_RETRIES})"
                    )
            except asyncio.TimeoutError:
                logger.warning(f"[{self.name}] Timeout on {url} (attempt {attempt})")
            except aiohttp.ClientError as e:
                logger.warning(f"[{self.name}] Client error on {url}: {e} (attempt {attempt})")
            except Exception as e:
                logger.error(f"[{self.name}] Unexpected error on {url}: {e}")
                break

            if attempt < self.settings.MAX_RETRIES:
                await asyncio.sleep(self.settings.RETRY_DELAY * attempt)

        return None

    async def _fetch_json(self, url: str, params: dict = None) -> Optional[dict]:
        """GET a URL and parse JSON response."""
        session = await self._get_session()

        for attempt in range(1, self.settings.MAX_RETRIES + 1):
            try:
                async with session.get(url, params=params, ssl=False) as resp:
                    if resp.status == 200:
                        return await resp.json(content_type=None)
                    logger.warning(
                        f"[{self.name}] HTTP {resp.status} for {url} "
                        f"(attempt {attempt}/{self.settings.MAX_RETRIES})"
                    )
            except Exception as e:
                logger.warning(f"[{self.name}] JSON fetch error: {e} (attempt {attempt})")

            if attempt < self.settings.MAX_RETRIES:
                await asyncio.sleep(self.settings.RETRY_DELAY * attempt)

        return None

    def _parse_html(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    def _safe_text(self, element) -> str:
        """Extract text from a BS4 element safely."""
        if element is None:
            return ""
        return element.get_text(strip=True)

    def _parse_date(self, date_str: str, formats: list = None) -> Optional[date]:
        """Try multiple date formats and return a date object."""
        if not date_str or not date_str.strip():
            return None

        default_formats = [
            "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d",
            "%d-%b-%Y", "%d %b %Y", "%d %B %Y",
            "%d-%m-%y", "%d/%m/%y",
        ]
        formats = formats or default_formats

        cleaned = date_str.strip().replace(".", "-")
        for fmt in formats:
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                continue
        return None

    # ── Abstract Interface ─────────────────────────────────────────────────

    @abstractmethod
    async def fetch_tenders(self) -> list[RawTender]:
        """Fetch and return all tenders from this portal."""
        ...

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
