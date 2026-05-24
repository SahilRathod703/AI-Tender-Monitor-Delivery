"""
scrapers/gem_scraper.py — GeM (Government e-Marketplace) scraper
GeM exposes a public bid/tender listing API.
API Base: https://bidplus.gem.gov.in/all-bids
"""

import logging
import re
from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

from scrapers.base_scraper import BaseScraper, RawTender

logger = logging.getLogger(__name__)


class GeMScraper(BaseScraper):
    """
    Scrapes GeM (Government e-Marketplace) bid listings.
    GeM hosts government procurement bids publicly accessible without login.
    """

    name = "GeM Portal"
    base_url = "https://bidplus.gem.gov.in"
    bid_list_url = "https://bidplus.gem.gov.in/all-bids"
    bid_search_url = "https://bidplus.gem.gov.in/search-bids"

    # GeM public API endpoints
    api_base = "https://bidplus.gem.gov.in/api/bidplus"

    # Tech-related product categories on GeM
    TECH_CATEGORIES = [
        "Information Technology",
        "Software",
        "Electronics",
        "Telecom Equipment",
        "Cloud Services",
        "Cybersecurity",
        "Hardware",
        "Networking Equipment",
        "Servers and Storage",
        "AI Services",
    ]

    async def fetch_tenders(self) -> list[RawTender]:
        tenders = []

        # Approach 1: Scrape bid listing pages
        tenders.extend(await self._scrape_bid_listing())

        # Approach 2: Category-based search
        tenders.extend(await self._search_by_categories())

        # Deduplicate
        seen = set()
        unique = []
        for t in tenders:
            key = t.unique_key()
            if key not in seen:
                seen.add(key)
                unique.append(t)

        logger.info(f"[{self.name}] Total unique bids: {len(unique)}")
        return unique

    async def _scrape_bid_listing(self) -> list[RawTender]:
        """Scrape the main bid listing on bidplus.gem.gov.in."""
        tenders = []
        today = date.today()
        cutoff = today - timedelta(days=self.settings.TENDER_LOOKBACK_DAYS)

        # GeM paginated bid list (page 1 = most recent)
        for page_num in range(1, 4):  # Check first 3 pages
            url = f"{self.bid_list_url}?page_no={page_num}"
            html = await self._fetch(url)
            if not html:
                break

            soup = self._parse_html(html)
            bid_cards = soup.select(".bid-info-container, div[class*='bid']")

            if not bid_cards:
                # Try table-based layout
                bid_cards = soup.select("tr.bid-row, .bid_listing tr")

            page_tenders = []
            for card in bid_cards:
                tender = self._parse_bid_card(card, today)
                if tender:
                    # Check if within lookback window
                    if tender.publish_date and tender.publish_date < cutoff:
                        continue
                    page_tenders.append(tender)

            if not page_tenders:
                break  # No more results

            tenders.extend(page_tenders)

            # If all tenders on this page are older than cutoff, stop paginating
            old_count = sum(
                1 for t in page_tenders
                if t.publish_date and t.publish_date < cutoff
            )
            if old_count == len(page_tenders):
                break

        logger.info(f"[{self.name}] Found {len(tenders)} bids from listing pages")
        return tenders

    def _parse_bid_card(self, card, today: date) -> Optional[RawTender]:
        """Parse a single bid card element."""
        try:
            # Title
            title_el = card.select_one(
                "h4, h3, .bid-title, a[class*='title'], span[class*='name']"
            )
            title = self._safe_text(title_el)
            if not title:
                return None

            # Link
            link_el = card.select_one("a[href*='bid'], a[href*='gem']")
            href = link_el.get("href", "") if link_el else ""
            url = f"{self.base_url}{href}" if href.startswith("/") else (href or self.base_url)

            # Bid ID
            bid_id_el = card.select_one(
                "[class*='bid-no'], [class*='bid_no'], span[class*='id']"
            )
            bid_id = self._safe_text(bid_id_el)
            if not bid_id:
                # Try extracting from URL
                m = re.search(r"GEM/\d{4}/B/\d+", url + title)
                bid_id = m.group(0) if m else None

            # Organization
            org_el = card.select_one(
                "[class*='ministry'], [class*='org'], [class*='dept']"
            )
            organization = self._safe_text(org_el) or "Government of India"

            # Dates
            date_els = card.select("[class*='date'], span[class*='time']")
            pub_date, deadline = None, None
            for el in date_els:
                text = self._safe_text(el).lower()
                date_val = self._parse_date(re.sub(r"[^0-9\-/]", "", text))
                if "start" in text or "publish" in text:
                    pub_date = date_val
                elif "end" in text or "close" in text or "last" in text:
                    deadline = date_val

            # Tender value
            value_el = card.select_one("[class*='value'], [class*='amount']")
            tender_value = self._safe_text(value_el) or None

            return RawTender(
                title=title,
                organization=organization,
                portal_source=self.name,
                govt_type="Central",
                state=None,
                url=url,
                publish_date=pub_date or today,
                deadline=deadline,
                tender_id=bid_id or title[:30],
                tender_value=tender_value,
                raw_description=title,
            )
        except Exception as e:
            logger.debug(f"[{self.name}] Card parse error: {e}")
            return None

    async def _search_by_categories(self) -> list[RawTender]:
        """Search GeM bids by technology product categories."""
        tenders = []

        for category in self.TECH_CATEGORIES[:5]:  # Limit to avoid hammering
            params = {
                "cat": category,
                "page_no": 1,
            }
            html = await self._fetch(self.bid_search_url, params=params)
            if not html:
                continue

            soup = self._parse_html(html)
            cards = soup.select(".bid-info-container, tr.bid-row")
            today = date.today()

            for card in cards:
                tender = self._parse_bid_card(card, today)
                if tender:
                    tender.category = category
                    tenders.append(tender)

        logger.info(f"[{self.name}] Found {len(tenders)} bids from category search")
        return tenders
