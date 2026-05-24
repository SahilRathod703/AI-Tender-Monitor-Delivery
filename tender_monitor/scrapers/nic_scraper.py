"""
scrapers/nic_scraper.py — NIC and other central govt portal scrapers.
Covers: NIC tenders, Railway e-procurement, PSU portals, Smart Cities.
"""

import logging
import re
from datetime import date, timedelta
from urllib.parse import urljoin

from scrapers.base_scraper import BaseScraper, RawTender

logger = logging.getLogger(__name__)


NIC_PORTALS = [
    {
        "name": "NIC Tenders",
        "org": "National Informatics Centre",
        "url": "https://www.nic.in/tenders/",
        "row_selector": "table tr, .tender-row, article.post",
        "govt_type": "Central",
        "state": None,
    },
    {
        "name": "IREPS (Railways)",
        "org": "Indian Railways",
        "url": "https://www.ireps.gov.in/ireps/aio.do?action=tenderSearch",
        "row_selector": "table#tenderTable tr, table.tender-list tr",
        "govt_type": "Central",
        "state": None,
    },
    {
        "name": "NTPC eTender",
        "org": "NTPC Limited",
        "url": "https://etender.ntpc.co.in/irj/portal",
        "row_selector": "table tr",
        "govt_type": "Central",
        "state": None,
    },
    {
        "name": "BHEL eProcurement",
        "org": "BHEL",
        "url": "https://www.bhel.com/tenders",
        "row_selector": "table tr, .tender-item, li.tender",
        "govt_type": "Central",
        "state": None,
    },
    {
        "name": "BSNL Tenders",
        "org": "BSNL",
        "url": "https://www.bsnl.co.in/opencms/BSNL/BSNL/about_us/tenders/index.html",
        "row_selector": "table tr, .content table tr",
        "govt_type": "Central",
        "state": None,
    },
    {
        "name": "MeitY Procurement",
        "org": "Ministry of Electronics and IT",
        "url": "https://www.meity.gov.in/tenders",
        "row_selector": "table tr, .views-row, article",
        "govt_type": "Central",
        "state": None,
    },
    {
        "name": "Smart Cities Mission",
        "org": "Smart Cities Mission",
        "url": "https://smartcities.gov.in/tenders",
        "row_selector": "table tr, .tender-card, .card",
        "govt_type": "Central",
        "state": None,
    },
    {
        "name": "STPI Tenders",
        "org": "Software Technology Parks of India",
        "url": "https://www.stpi.in/tenders",
        "row_selector": "table tr, .tender-row",
        "govt_type": "Central",
        "state": None,
    },
    {
        "name": "C-DAC Tenders",
        "org": "Centre for Development of Advanced Computing",
        "url": "https://www.cdac.in/index.aspx?id=tenders",
        "row_selector": "table tr, .tender-list li",
        "govt_type": "Central",
        "state": None,
    },
    {
        "name": "DRDO Procurement",
        "org": "Defence Research and Development Organisation",
        "url": "https://www.drdo.gov.in/procurement-notices",
        "row_selector": "table tr, .views-row, .field-items",
        "govt_type": "Central",
        "state": None,
    },
]


class NICScraper(BaseScraper):
    """
    Scrapes NIC-hosted and other central government portals.
    """

    name = "NIC & Central PSUs"

    async def fetch_tenders(self) -> list[RawTender]:
        all_tenders = []

        for portal in NIC_PORTALS:
            try:
                tenders = await self._scrape_portal(portal)
                all_tenders.extend(tenders)
                if tenders:
                    logger.info(f"[NIC] {portal['name']}: {len(tenders)} tenders")
            except Exception as e:
                logger.error(f"[NIC] Failed {portal['name']}: {e}")

        return all_tenders

    async def _scrape_portal(self, config: dict) -> list[RawTender]:
        """Generic scraper that works across NIC-style portals."""
        tenders = []
        html = await self._fetch(config["url"])
        if not html:
            return tenders

        soup = self._parse_html(html)
        today = date.today()
        cutoff = today - timedelta(days=self.settings.TENDER_LOOKBACK_DAYS)

        elements = soup.select(config["row_selector"])

        for el in elements:
            try:
                tender = self._parse_element(el, config, today)
                if tender:
                    if tender.publish_date and tender.publish_date >= cutoff:
                        tenders.append(tender)
                    elif not tender.publish_date:
                        # No date found — include and let filter decide
                        tenders.append(tender)
            except Exception as e:
                logger.debug(f"[NIC:{config['name']}] Element error: {e}")
                continue

        return tenders

    def _parse_element(self, el, config: dict, today: date) -> RawTender:
        """Parse a tender element (tr, article, div, li, etc.)."""
        # Get all text content
        full_text = self._safe_text(el)
        if not full_text or len(full_text) < 10:
            return None

        # Title: prefer anchor text or first significant text
        link = el.find("a")
        title = self._safe_text(link) if link else full_text[:120]

        if not title or len(title) < 5:
            return None

        # URL
        href = link.get("href", "") if link else ""
        url = (
            urljoin(config["url"], href)
            if href and not href.startswith("http")
            else (href or config["url"])
        )

        # Dates — try to extract from text
        pub_date, deadline = self._extract_dates_from_text(full_text, today)

        # Organization
        org_el = el.select_one(
            "[class*='org'], [class*='dept'], [class*='ministry']"
        )
        organization = self._safe_text(org_el) or config["org"]

        # Tender value
        value_match = re.search(
            r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d+)?\s*(?:Crore|Lakh|Cr|L|K)?",
            full_text,
            re.IGNORECASE,
        )
        tender_value = value_match.group(0) if value_match else None

        # ID
        import hashlib
        tid = hashlib.md5(
            (config["name"] + title).encode()
        ).hexdigest()[:12]

        return RawTender(
            title=title,
            organization=organization,
            portal_source=config["name"],
            govt_type=config["govt_type"],
            state=config.get("state"),
            url=url,
            publish_date=pub_date or today,
            deadline=deadline,
            tender_id=tid,
            tender_value=tender_value,
            raw_description=full_text[:500],
        )

    def _extract_dates_from_text(self, text: str, today: date):
        """Extract publication and deadline dates from raw text."""
        # Look for date patterns
        date_pattern = re.compile(
            r"\b(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{1,2}\s+\w{3,9}\s+\d{4})\b"
        )
        dates_found = [
            self._parse_date(m.group())
            for m in date_pattern.finditer(text)
        ]
        dates_found = [d for d in dates_found if d]  # remove None

        if not dates_found:
            return None, None

        # Heuristic: earliest date = pub_date, latest = deadline
        dates_found.sort()
        pub_date = dates_found[0] if dates_found[0] <= today else None
        deadline = dates_found[-1] if len(dates_found) > 1 else None

        return pub_date, deadline
