"""
reporters/sheets_reporter.py — Appends tender data to a Google Sheet.
Requires: google-auth, gspread
"""

import logging
from datetime import datetime
from typing import Optional

from scrapers.base_scraper import RawTender

logger = logging.getLogger(__name__)

SHEET_HEADERS = [
    "Report Date",
    "Tender Title",
    "Organization",
    "Govt Type",
    "State",
    "Portal Source",
    "Publish Date",
    "Deadline",
    "Tender Value",
    "Matched Keywords",
    "AI Summary",
    "Official Link",
    "Tender ID",
]


class SheetsReporter:
    name = "Google Sheets"

    def __init__(self, settings):
        self.settings = settings
        self._client = None
        self._sheet = None

    def _get_client(self):
        """Lazy-init gspread client."""
        if self._client is None:
            import gspread
            from google.oauth2.service_account import Credentials

            SCOPES = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(
                self.settings.GOOGLE_CREDENTIALS_PATH, scopes=SCOPES
            )
            self._client = gspread.authorize(creds)
        return self._client

    def _get_sheet(self):
        """Get or create the tender worksheet."""
        if self._sheet is None:
            client = self._get_client()
            spreadsheet = client.open_by_key(self.settings.GOOGLE_SHEET_ID)

            # Try to get existing sheet; create if not found
            try:
                self._sheet = spreadsheet.worksheet("Tenders")
            except Exception:
                self._sheet = spreadsheet.add_worksheet(
                    title="Tenders", rows=10000, cols=len(SHEET_HEADERS)
                )
                # Add headers
                self._sheet.append_row(SHEET_HEADERS)
                self._sheet.format(
                    "A1:M1",
                    {
                        "backgroundColor": {"red": 0.12, "green": 0.23, "blue": 0.37},
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                    },
                )
        return self._sheet

    async def send_report(self, tenders: list[RawTender]):
        if not tenders:
            return

        try:
            sheet = self._get_sheet()
            now = datetime.now().strftime("%Y-%m-%d %H:%M IST")

            rows = []
            for t in tenders:
                rows.append([
                    now,
                    t.title,
                    t.organization,
                    t.govt_type,
                    t.state or "Central",
                    t.portal_source,
                    str(t.publish_date or ""),
                    str(t.deadline or ""),
                    t.tender_value or "N/A",
                    ", ".join(t.matched_keywords[:5]) if t.matched_keywords else "",
                    t.ai_summary or "",
                    t.url,
                    t.tender_id or "",
                ])

            # Batch append (more efficient than one-by-one)
            sheet.append_rows(rows, value_input_option="RAW")

            logger.info(
                f"[Sheets] Appended {len(rows)} rows to Google Sheet "
                f"(ID: {self.settings.GOOGLE_SHEET_ID})"
            )
            return True

        except Exception as e:
            logger.error(f"[Sheets] Failed to update Google Sheet: {e}")
            return False
