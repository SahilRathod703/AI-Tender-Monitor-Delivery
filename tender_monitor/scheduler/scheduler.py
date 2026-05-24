"""
scheduler/scheduler.py — Daily scheduler for the Tender Monitor.
Runs at 10:00 AM IST and 7:00 PM IST every day.
IST = UTC + 5:30, so these map to UTC 04:30 and 13:30.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")


class TenderScheduler:
    """Schedules tender monitoring cycles at configured IST times."""

    def __init__(self, monitor_system):
        self.system = monitor_system
        self.scheduler = BlockingScheduler(timezone=IST)
        self._setup_jobs()
        self._setup_signals()

    def _setup_jobs(self):
        """Register scheduled jobs from settings."""
        times = self.system.settings.SCHEDULE_TIMES_IST

        for i, time_config in enumerate(times):
            hour = time_config["hour"]
            minute = time_config.get("minute", 0)

            self.scheduler.add_job(
                self._run_async_cycle,
                trigger=CronTrigger(
                    hour=hour,
                    minute=minute,
                    timezone=IST,
                ),
                id=f"tender_monitor_{i}",
                name=f"Tender Monitor — {hour:02d}:{minute:02d} IST",
                misfire_grace_time=300,         # 5 min grace if system was sleeping
                coalesce=True,                  # If missed multiple, run only once
                max_instances=1,                # No concurrent runs
            )
            logger.info(
                f"Scheduled: tender scan at {hour:02d}:{minute:02d} IST daily"
            )

    def _run_async_cycle(self):
        """Bridge between APScheduler (sync) and our async code."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.system.run_cycle())
        finally:
            loop.close()

    def _setup_signals(self):
        """Graceful shutdown on Ctrl+C / SIGTERM."""
        def _shutdown(signum, frame):
            logger.info("Shutdown signal received. Stopping scheduler...")
            self.scheduler.shutdown(wait=False)
            sys.exit(0)

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

    def start(self):
        """Start the scheduler and block until stopped."""
        now_ist = datetime.now(IST)
        logger.info("=" * 60)
        logger.info("AI Tender Monitor — Scheduler Started")
        logger.info(f"Current IST time: {now_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info("Scheduled runs: 10:00 AM IST and 07:00 PM IST daily")
        logger.info("Press Ctrl+C to stop.")
        logger.info("=" * 60)

        self.scheduler.start()

    def trigger_now(self):
        """Manually trigger a run (for testing)."""
        logger.info("Manual trigger: running cycle now")
        self._run_async_cycle()
