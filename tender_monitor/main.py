"""
AI Tender Monitoring System - Main Entry Point
Runs automated tender discovery from Indian Government portals
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import Settings
from database.db import Database
from processors.filter import TenderFilter
from processors.summarizer import TenderSummarizer
from reporters.email_reporter import EmailReporter
from reporters.sheets_reporter import SheetsReporter
from scrapers.cppp_scraper import CPPPScraper
from scrapers.gem_scraper import GeMScraper
from scrapers.state_scraper import StatePortalScraper
from scrapers.nic_scraper import NICScraper
from scheduler.scheduler import TenderScheduler
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TenderMonitorSystem:
    """Core orchestrator for the tender monitoring system."""

    def __init__(self):
        self.settings = Settings()
        self.db = Database(self.settings.DATABASE_URL)
        self.filter = TenderFilter(self.settings.KEYWORDS)
        self.summarizer = TenderSummarizer(self.settings.ANTHROPIC_API_KEY)
        self.reporters = self._init_reporters()
        self.scrapers = self._init_scrapers()

    def _init_reporters(self):
        reporters = []
        if self.settings.EMAIL_ENABLED:
            reporters.append(EmailReporter(self.settings))
        if self.settings.SHEETS_ENABLED:
            reporters.append(SheetsReporter(self.settings))
        return reporters

    def _init_scrapers(self):
        return [
            CPPPScraper(self.settings),
            GeMScraper(self.settings),
            NICScraper(self.settings),
            StatePortalScraper(self.settings),
        ]

    async def run_cycle(self):
        """Execute one complete monitoring cycle."""
        logger.info("=" * 60)
        logger.info("Starting tender monitoring cycle")
        logger.info("=" * 60)

        all_tenders = []

        # Step 1: Scrape all portals
        for scraper in self.scrapers:
            try:
                logger.info(f"Scraping: {scraper.name}")
                tenders = await scraper.fetch_tenders()
                all_tenders.extend(tenders)
                logger.info(f"  → Found {len(tenders)} tenders from {scraper.name}")
            except Exception as e:
                logger.error(f"  ✗ Failed to scrape {scraper.name}: {e}")

        logger.info(f"\nTotal raw tenders fetched: {len(all_tenders)}")

        # Step 2: Filter relevant tenders
        relevant = self.filter.filter(all_tenders)
        logger.info(f"Relevant tenders after filtering: {len(relevant)}")

        # Step 3: Remove duplicates (already in DB)
        new_tenders = self.db.filter_new(relevant)
        logger.info(f"New tenders (not yet reported): {len(new_tenders)}")

        if not new_tenders:
            logger.info("No new tenders to report. Cycle complete.")
            return

        # Step 4: AI summarization
        logger.info("Generating AI summaries...")
        summarized = await self.summarizer.summarize_batch(new_tenders)

        # Step 5: Save to database
        self.db.save_tenders(summarized)
        logger.info(f"Saved {len(summarized)} tenders to database")

        # Step 6: Send reports
        for reporter in self.reporters:
            try:
                await reporter.send_report(summarized)
                logger.info(f"Report sent via {reporter.name}")
            except Exception as e:
                logger.error(f"Failed to send report via {reporter.name}: {e}")

        logger.info("=" * 60)
        logger.info(f"Cycle complete. Reported {len(summarized)} new tenders.")
        logger.info("=" * 60)

    async def run_once(self):
        """Run a single cycle (for testing or manual trigger)."""
        self.db.initialize()
        await self.run_cycle()

    def start_scheduler(self):
        """Start the scheduled automation (10 AM and 7 PM IST daily)."""
        self.db.initialize()
        scheduler = TenderScheduler(self)
        scheduler.start()


# ─── CLI Entry Points ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Tender Monitoring System")
    parser.add_argument(
        "--mode",
        choices=["run-once", "scheduler"],
        default="scheduler",
        help="run-once: single fetch cycle | scheduler: start daily automation",
    )
    args = parser.parse_args()

    system = TenderMonitorSystem()

    if args.mode == "run-once":
        asyncio.run(system.run_once())
    else:
        system.start_scheduler()
