"""
scrapers/cppp_scraper.py — Central Public Procurement Portal scraper
Portal: https://eprocure.gov.in/eprocure/app
API:    https://eprocure.gov.in (search endpoint)
"""

import logging
from datetime import date, timedelta
from urllib.parse import urljoin

from scrapers.base_scraper import BaseScraper, RawTender

logger = logging.getLogger(__name__)


class CPPPScraper(BaseScraper):
    """
    Scrapes the Central Public Procurement Portal (eProcure).
    Uses the public search interface — no login required for listing.
    """

    name = "CPPP (eProcure)"
    base_url = "https://eprocure.gov.in"
    search_url = "https://eprocure.gov.in/eprocure/app?component=%24DirectLink&page=FrontEndTendersByOrganisationList&service=direct&session=T&sp=SFront+End+Tenders+By+Organisation+List"

    # Alternative: use the open NIC API endpoint
    nic_api_url = "https://eprocure.gov.in/eprocure/app"

    async def fetch_tenders(self) -> list[RawTender]:
        tenders = []

        # Strategy 1: Scrape the public tender search page
        tenders.extend(await self._scrape_active_tenders())

        # Strategy 2: Try the technology-specific category search
        tenders.extend(await self._scrape_by_category())

        # Deduplicate by tender_id
        seen = set()
        unique = []
        for t in tenders:
            if t.unique_key() not in seen:
                seen.add(t.unique_key())
                unique.append(t)

        return unique

    async def _scrape_active_tenders(self) -> list[RawTender]:
        """Scrape the main active tenders listing page."""
        tenders = []
        today = date.today()
        cutoff = today - timedelta(days=self.settings.TENDER_LOOKBACK_DAYS)

        # Try fetching the technology tender search
        search_params = {
            "component": "$DirectLink",
            "page": "FrontEndAdvancedSearch",
            "service": "direct",
        }

        html = await self._fetch(self.nic_api_url, params=search_params)
        if not html:
            logger.warning(f"[{self.name}] Could not reach main portal")
            return tenders

        soup = self._parse_html(html)

        # Parse tender table rows
        rows = soup.select("table.list_table tr, table tr.even, table tr.odd")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            try:
                tender_link = row.find("a")
                if not tender_link:
                    continue

                title = self._safe_text(tender_link)
                href = tender_link.get("href", "")
                url = urljoin(self.base_url, href) if href else self.base_url

                # Extract dates from columns
                pub_date_str = self._safe_text(cols[2]) if len(cols) > 2 else ""
                deadline_str = self._safe_text(cols[3]) if len(cols) > 3 else ""
                org = self._safe_text(cols[1]) if len(cols) > 1 else ""

                pub_date = self._parse_date(pub_date_str)
                deadline = self._parse_date(deadline_str)

                # Only include tenders published within lookback window
                if pub_date and pub_date < cutoff:
                    continue

                # Extract tender ID from URL or text
                tender_id = self._extract_tender_id(href or title)

                tender = RawTender(
                    title=title,
                    organization=org or "Central Government",
                    portal_source=self.name,
                    govt_type="Central",
                    state=None,
                    url=url,
                    publish_date=pub_date or today,
                    deadline=deadline,
                    tender_id=tender_id,
                    raw_description=title,  # Description scraped from title
                )
                tenders.append(tender)

            except Exception as e:
                logger.debug(f"[{self.name}] Row parse error: {e}")
                continue

        logger.info(f"[{self.name}] Scraped {len(tenders)} tenders from main listing")
        return tenders

    async def _scrape_by_category(self) -> list[RawTender]:
        """Search by IT/Technology category using CPPP's search."""
        tenders = []

        # Technology-related product categories on CPPP
        tech_categories = ["IT", "Software", "Electronics", "Telecom"]

        for category in tech_categories:
            html = await self._fetch(
                self.nic_api_url,
                params={
                    "component": "$DirectLink",
                    "page": "FrontEndAdvancedSearch",
                    "service": "direct",
                    "productCategory": category,
                },
            )
            if not html:
                continue

            soup = self._parse_html(html)
            rows = soup.select("table.list_table tr")

            for row in rows[1:]:  # skip header
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue
                try:
                    link = row.find("a")
                    if not link:
                        continue
                    title = self._safe_text(link)
                    href = link.get("href", "")
                    url = urljoin(self.base_url, href)
                    org = self._safe_text(cols[1]) if len(cols) > 1 else ""
                    deadline_str = self._safe_text(cols[-1])
                    deadline = self._parse_date(deadline_str)

                    tenders.append(RawTender(
                        title=title,
                        organization=org,
                        portal_source=self.name,
                        govt_type="Central",
                        state=None,
                        url=url,
                        publish_date=date.today(),
                        deadline=deadline,
                        tender_id=self._extract_tender_id(href),
                        category=category,
                    ))
                except Exception:
                    continue

        return tenders

    def _extract_tender_id(self, text: str) -> str:
        """Extract tender ID from URL parameters or text."""
        import re
        # Look for patterns like 2024_DRDO_123456_1
        patterns = [
            r"(\d{4}_[A-Z]+_\d+_\d+)",
            r"tenderId=(\w+)",
            r"tender_id=(\w+)",
            r"/(\d{10,})",
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                return m.group(1)
        # Fallback: hash the URL
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()[:12]
