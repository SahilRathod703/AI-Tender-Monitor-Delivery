"""
scrapers/state_scraper.py — Multi-state eProcurement portal scraper.
Covers major Indian state government procurement portals.
"""

import logging
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from scrapers.base_scraper import BaseScraper, RawTender

logger = logging.getLogger(__name__)


# Registry of state portals with their scraping config
STATE_PORTALS = [
    {
        "name": "Karnataka eProcurement",
        "state": "Karnataka",
        "url": "https://eproc.karnataka.gov.in/eprocurement/app",
        "tender_list_path": "?component=$DirectLink&page=FrontEndTendersByOrganisationList",
        "row_selector": "table.list_table tr",
        "cols": {"title": 0, "org": 1, "pub_date": 2, "deadline": 3},
    },
    {
        "name": "Tamil Nadu eTenders",
        "state": "Tamil Nadu",
        "url": "https://tntenders.gov.in/nicgep/app",
        "tender_list_path": "?component=$DirectLink&page=FrontEndTendersByOrganisationList",
        "row_selector": "table tr",
        "cols": {"title": 1, "org": 2, "pub_date": 3, "deadline": 4},
    },
    {
        "name": "Maharashtra GovTenders",
        "state": "Maharashtra",
        "url": "https://mahatenders.gov.in/nicgep/app",
        "tender_list_path": "?component=$DirectLink&page=FrontEndAdvancedSearch",
        "row_selector": "table.tablesorter tr",
        "cols": {"title": 1, "org": 2, "pub_date": 3, "deadline": 4},
    },
    {
        "name": "Rajasthan eProcurement",
        "state": "Rajasthan",
        "url": "https://sppp.rajasthan.gov.in/nicgep/app",
        "tender_list_path": "?component=$DirectLink&page=FrontEndTendersByOrganisationList",
        "row_selector": "table tr",
        "cols": {"title": 1, "org": 0, "pub_date": 2, "deadline": 3},
    },
    {
        "name": "Gujarat eProcurement",
        "state": "Gujarat",
        "url": "https://tender.nprocure.com",
        "tender_list_path": "/TenderList.aspx",
        "row_selector": "table#grdTender tr",
        "cols": {"title": 1, "org": 2, "pub_date": 4, "deadline": 5},
    },
    {
        "name": "Telangana eProcurement",
        "state": "Telangana",
        "url": "https://eprocurement.telangana.gov.in/tenders",
        "tender_list_path": "",
        "row_selector": "table tr",
        "cols": {"title": 1, "org": 2, "pub_date": 3, "deadline": 4},
    },
    {
        "name": "Andhra Pradesh eProcurement",
        "state": "Andhra Pradesh",
        "url": "https://tender.apeprocurement.gov.in",
        "tender_list_path": "",
        "row_selector": "table.table tr",
        "cols": {"title": 1, "org": 2, "pub_date": 3, "deadline": 4},
    },
    {
        "name": "Kerala eTenders",
        "state": "Kerala",
        "url": "https://etenders.kerala.gov.in/nicgep/app",
        "tender_list_path": "?component=$DirectLink&page=FrontEndTendersByOrganisationList",
        "row_selector": "table tr",
        "cols": {"title": 0, "org": 1, "pub_date": 2, "deadline": 3},
    },
    {
        "name": "UP eProcurement",
        "state": "Uttar Pradesh",
        "url": "https://etender.up.nic.in/nicgep/app",
        "tender_list_path": "?component=$DirectLink&page=FrontEndTendersByOrganisationList",
        "row_selector": "table.list_table tr",
        "cols": {"title": 0, "org": 1, "pub_date": 2, "deadline": 3},
    },
    {
        "name": "MP eTenders",
        "state": "Madhya Pradesh",
        "url": "https://www.mptenders.gov.in/nicgep/app",
        "tender_list_path": "?component=$DirectLink&page=FrontEndTendersByOrganisationList",
        "row_selector": "table tr",
        "cols": {"title": 1, "org": 0, "pub_date": 2, "deadline": 3},
    },
]


class StatePortalScraper(BaseScraper):
    """Scrapes multiple Indian state government eProcurement portals."""

    name = "State Portals"

    async def fetch_tenders(self) -> list[RawTender]:
        all_tenders = []

        for portal_config in STATE_PORTALS:
            try:
                tenders = await self._scrape_portal(portal_config)
                all_tenders.extend(tenders)
                logger.info(
                    f"[State] {portal_config['name']}: {len(tenders)} tenders"
                )
            except Exception as e:
                logger.error(
                    f"[State] Failed to scrape {portal_config['name']}: {e}"
                )

        return all_tenders

    async def _scrape_portal(self, config: dict) -> list[RawTender]:
        """Scrape a single state portal using its config."""
        tenders = []
        url = config["url"] + config.get("tender_list_path", "")
        html = await self._fetch(url)

        if not html:
            return tenders

        soup = self._parse_html(html)
        today = date.today()
        cutoff = today - timedelta(days=self.settings.TENDER_LOOKBACK_DAYS)

        rows = soup.select(config["row_selector"])
        cols_map = config["cols"]

        for row in rows[1:]:  # Skip header row
            cols = row.find_all("td")
            if len(cols) < 2:
                continue

            try:
                title_idx = cols_map.get("title", 0)
                org_idx = cols_map.get("org", 1)
                pub_idx = cols_map.get("pub_date", 2)
                dl_idx = cols_map.get("deadline", 3)

                title_el = cols[title_idx] if title_idx < len(cols) else None
                title = self._safe_text(title_el)
                if not title:
                    continue

                # URL from link in title cell
                link = title_el.find("a") if title_el else None
                href = link.get("href", "") if link else ""
                tender_url = urljoin(config["url"], href) if href else config["url"]

                org = (
                    self._safe_text(cols[org_idx])
                    if org_idx < len(cols)
                    else config["state"] + " Government"
                )

                pub_str = (
                    self._safe_text(cols[pub_idx])
                    if pub_idx < len(cols)
                    else ""
                )
                dl_str = (
                    self._safe_text(cols[dl_idx])
                    if dl_idx < len(cols)
                    else ""
                )

                pub_date = self._parse_date(pub_str)
                deadline = self._parse_date(dl_str)

                if pub_date and pub_date < cutoff:
                    continue

                # Tender ID
                import hashlib
                tid = hashlib.md5(
                    (config["state"] + title).encode()
                ).hexdigest()[:12]

                tenders.append(RawTender(
                    title=title,
                    organization=org,
                    portal_source=config["name"],
                    govt_type="State",
                    state=config["state"],
                    url=tender_url,
                    publish_date=pub_date or today,
                    deadline=deadline,
                    tender_id=tid,
                    raw_description=title,
                ))

            except Exception as e:
                logger.debug(f"[State:{config['name']}] Row error: {e}")
                continue

        return tenders
