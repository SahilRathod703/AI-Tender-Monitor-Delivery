"""
config/settings.py — Central configuration for the Tender Monitor
All secrets come from environment variables or a .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv(Path(__file__).parent.parent / ".env")


class Settings:
    # ── Project Paths ──────────────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/tenders.db")

    # ── Anthropic (Claude) API ─────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # ── Email Reporter ─────────────────────────────────────────────────────
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")          # App password for Gmail
    EMAIL_RECIPIENTS: list = os.getenv("EMAIL_RECIPIENTS", "").split(",")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))

    # ── Google Sheets Reporter ─────────────────────────────────────────────
    SHEETS_ENABLED: bool = os.getenv("SHEETS_ENABLED", "false").lower() == "true"
    GOOGLE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")

    # ── Scraper Settings ───────────────────────────────────────────────────
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "5.0"))   # seconds
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # ── Scheduler ─────────────────────────────────────────────────────────
    # Times in IST (UTC+5:30). APScheduler runs in UTC internally.
    SCHEDULE_TIMES_IST: list = [
        {"hour": 10, "minute": 0},   # 10:00 AM IST
        {"hour": 19, "minute": 0},   # 07:00 PM IST
    ]

    # ── Filtering ─────────────────────────────────────────────────────────
    from config.keywords import KEYWORDS
    KEYWORDS: list = KEYWORDS

    # ── Lookback Window ────────────────────────────────────────────────────
    # How many days back to consider a tender "new"
    TENDER_LOOKBACK_DAYS: int = int(os.getenv("TENDER_LOOKBACK_DAYS", "1"))

    # ── AI Summarizer ─────────────────────────────────────────────────────
    SUMMARIZER_MODEL: str = "claude-opus-4-5"
    MAX_SUMMARY_TOKENS: int = 300

    def __post_init__(self):
        # Ensure data and logs directories exist
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
