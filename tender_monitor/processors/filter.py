"""
processors/filter.py — Keyword-based tender relevance filter.
Applies both inclusion keywords and exclusion keywords.
"""

import logging
import re
from config.keywords import EXCLUSION_KEYWORDS
from scrapers.base_scraper import RawTender

logger = logging.getLogger(__name__)


class TenderFilter:
    """Filters tenders by keyword relevance."""

    def __init__(self, keywords: list[str]):
        # Pre-compile all patterns for performance
        self.include_patterns = [
            re.compile(r"\b" + re.escape(kw.lower()) + r"\b")
            for kw in keywords
        ]
        self.exclude_patterns = [
            re.compile(r"\b" + re.escape(kw.lower()) + r"\b")
            for kw in EXCLUSION_KEYWORDS
        ]

    def filter(self, tenders: list[RawTender]) -> list[RawTender]:
        """Return only tenders that match inclusion keywords."""
        relevant = []
        for tender in tenders:
            matched_keywords = self._match(tender)
            if matched_keywords:
                tender.matched_keywords = matched_keywords
                relevant.append(tender)

        logger.info(
            f"Filter: {len(tenders)} → {len(relevant)} relevant tenders"
        )
        return relevant

    def _match(self, tender: RawTender) -> list[str]:
        """
        Return list of matched keywords if tender is relevant, else empty list.
        """
        # Build searchable text from all available fields
        searchable = " ".join(filter(None, [
            tender.title,
            tender.raw_description,
            tender.category,
            tender.organization,
        ])).lower()

        # Exclusion check first
        for exc_pattern in self.exclude_patterns:
            title_text = tender.title.lower()
            if exc_pattern.search(title_text):
                # Only exclude if the tender is PRIMARILY about the excluded topic
                # (i.e., exclusion keyword is in the title, not just description)
                logger.debug(
                    f"Excluded by '{exc_pattern.pattern}': {tender.title[:60]}"
                )
                return []

        # Inclusion check
        matched = []
        for i, pattern in enumerate(self.include_patterns):
            if pattern.search(searchable):
                from config.keywords import KEYWORDS
                matched.append(KEYWORDS[i] if i < len(KEYWORDS) else pattern.pattern)

        return matched
