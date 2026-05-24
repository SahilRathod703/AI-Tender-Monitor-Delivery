"""
database/db.py — Database layer for tender storage and deduplication.
Supports SQLite (default) and PostgreSQL.
"""

import logging
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from scrapers.base_scraper import RawTender

logger = logging.getLogger(__name__)


# ─── ORM Models ──────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


class TenderRecord(Base):
    __tablename__ = "tenders"

    unique_key    = Column(String(255), primary_key=True)
    tender_id     = Column(String(100), nullable=True, index=True)
    title         = Column(Text, nullable=False)
    organization  = Column(String(500))
    portal_source = Column(String(200))
    govt_type     = Column(String(50))          # Central / State
    state         = Column(String(100))
    url           = Column(Text)
    publish_date  = Column(Date)
    deadline      = Column(Date)
    tender_value  = Column(String(200))
    category      = Column(String(200))
    raw_description = Column(Text)
    ai_summary    = Column(Text)
    matched_keywords = Column(Text)             # JSON array stored as string
    reported      = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=datetime.utcnow)


class ReportLog(Base):
    __tablename__ = "report_log"

    id          = Column(String(36), primary_key=True)  # UUID
    report_type = Column(String(50))                    # email / sheets
    reported_at = Column(DateTime, default=datetime.utcnow)
    tender_count = Column(String(10))
    status      = Column(String(50))                    # success / failed
    error_msg   = Column(Text, nullable=True)


# ─── Database Class ───────────────────────────────────────────────────────────

class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None

    def initialize(self):
        """Create tables and engine."""
        connect_args = {}
        if "sqlite" in self.database_url:
            connect_args["check_same_thread"] = False

        self.engine = create_engine(
            self.database_url,
            connect_args=connect_args,
            echo=False,
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Database initialized: {self.database_url}")

    def _session(self) -> Session:
        return self.SessionLocal()

    # ── Core Operations ──────────────────────────────────────────────────────

    def filter_new(self, tenders: list[RawTender]) -> list[RawTender]:
        """Return only tenders not already in the database."""
        keys = [t.unique_key() for t in tenders]

        with self._session() as session:
            existing = {
                row.unique_key
                for row in session.query(TenderRecord.unique_key)
                .filter(TenderRecord.unique_key.in_(keys))
                .all()
            }

        new_tenders = [t for t in tenders if t.unique_key() not in existing]
        logger.info(
            f"Duplicate check: {len(tenders)} tenders → "
            f"{len(new_tenders)} new, {len(existing)} already seen"
        )
        return new_tenders

    def save_tenders(self, tenders: list[RawTender]) -> int:
        """Save tenders to database. Returns count saved."""
        import json

        saved = 0
        with self._session() as session:
            for t in tenders:
                try:
                    record = TenderRecord(
                        unique_key=t.unique_key(),
                        tender_id=t.tender_id,
                        title=t.title,
                        organization=t.organization,
                        portal_source=t.portal_source,
                        govt_type=t.govt_type,
                        state=t.state,
                        url=t.url,
                        publish_date=t.publish_date,
                        deadline=t.deadline,
                        tender_value=t.tender_value,
                        category=t.category,
                        raw_description=t.raw_description,
                        ai_summary=t.ai_summary,
                        matched_keywords=json.dumps(t.matched_keywords),
                        reported=True,
                    )
                    session.merge(record)
                    saved += 1
                except Exception as e:
                    logger.error(f"Failed to save tender '{t.title[:50]}': {e}")

            session.commit()

        logger.info(f"Saved {saved} tenders to database")
        return saved

    def get_all_tenders(
        self,
        limit: int = 100,
        offset: int = 0,
        govt_type: Optional[str] = None,
        state: Optional[str] = None,
        since: Optional[date] = None,
    ) -> list[TenderRecord]:
        """Query tenders with optional filters."""
        with self._session() as session:
            query = session.query(TenderRecord)

            if govt_type:
                query = query.filter(TenderRecord.govt_type == govt_type)
            if state:
                query = query.filter(TenderRecord.state == state)
            if since:
                query = query.filter(TenderRecord.publish_date >= since)

            return (
                query.order_by(TenderRecord.created_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

    def get_stats(self) -> dict:
        """Return summary statistics."""
        with self._session() as session:
            total = session.query(TenderRecord).count()
            central = (
                session.query(TenderRecord)
                .filter(TenderRecord.govt_type == "Central")
                .count()
            )
            state = (
                session.query(TenderRecord)
                .filter(TenderRecord.govt_type == "State")
                .count()
            )
            today_count = (
                session.query(TenderRecord)
                .filter(TenderRecord.publish_date == date.today())
                .count()
            )

        return {
            "total": total,
            "central": central,
            "state": state,
            "today": today_count,
        }

    def log_report(
        self,
        report_type: str,
        tender_count: int,
        status: str,
        error_msg: str = None,
    ):
        """Log a reporting event."""
        import uuid
        with self._session() as session:
            session.add(ReportLog(
                id=str(uuid.uuid4()),
                report_type=report_type,
                tender_count=str(tender_count),
                status=status,
                error_msg=error_msg,
            ))
            session.commit()
