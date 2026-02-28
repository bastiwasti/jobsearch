"""Job listing data model used throughout the scraping pipeline."""

from dataclasses import dataclass, field


@dataclass
class JobListing:
    """Structured job listing extracted from a site.

    Passed from parser → filter → dedup → database insertion.
    """

    title: str
    company: str
    url: str
    source_site: str
    location: str = ""
    description: str = ""
    salary: str = ""
    job_type: str = ""        # full-time, part-time, contract, internship, freelance
    remote: str = ""          # remote, hybrid, on-site
    posted_date: str = ""     # ISO date string
    raw_data: dict | None = field(default=None, repr=False)
