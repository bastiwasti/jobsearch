"""SQLAlchemy ORM models for the JobSearch database.

Note: The scraper now saves ALL jobs that pass EXCLUDE filters.
INCLUDE patterns have been removed to collect broader data for later refinement.

EXCLUDE filters: Junior, Trainee, Praktikum, Werkstudent, unpaid, volunteer
Location filters: Remote jobs (80-100%) or Rheinland (~50km from Monheim)
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True)
    title = Column(Text, nullable=False)
    company = Column(Text, nullable=False)
    location = Column(Text, default="")
    url = Column(Text, nullable=False, unique=True)
    description = Column(Text, default="")
    salary = Column(Text, default="")
    job_type = Column(String(50), default="")        # full-time, part-time, etc.
    remote = Column(String(50), default="")           # remote, hybrid, on-site
    posted_date = Column(DateTime(timezone=True), nullable=True)
    source_site = Column(String(100), nullable=False)
    extraction_method = Column(String(20), default="css")  # css, llm

    raw_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Single-user features
    is_bookmarked = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)
    notes = Column(Text, default="")
    applied_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="new")        # new, interested, applied, interviewing, rejected, offer
    refined_at = Column(DateTime(timezone=True), nullable=True)

    run = relationship("ScrapeRun", back_populates="jobs")

    __table_args__ = (
        Index("idx_jobs_source", "source_site"),
        Index("idx_jobs_created", created_at.desc()),
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_bookmarked", "is_bookmarked", postgresql_where=(is_bookmarked == True)),
    )


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="running")    # running, completed, failed
    sites_scraped = Column(Integer, default=0)
    jobs_found = Column(Integer, default=0)            # total parsed from pages
    jobs_matched = Column(Integer, default=0)           # jobs that passed EXCLUDE filters (jobs stored)
    jobs_new = Column(Integer, default=0)               # inserted (not dupes)
    errors = Column(JSONB, nullable=True)               # [{site, error}]
    trigger = Column(String(50), default="manual")      # manual, scheduled, api

    jobs = relationship("Job", back_populates="run")
