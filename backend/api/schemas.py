"""Pydantic request/response models for the API."""

from datetime import datetime
from pydantic import BaseModel


class JobResponse(BaseModel):
    id: int
    run_id: int | None
    title: str
    company: str
    location: str
    url: str
    description: str
    salary: str
    job_type: str
    remote: str
    posted_date: datetime | None
    source_site: str
    extraction_method: str
    created_at: datetime
    is_bookmarked: bool
    is_hidden: bool
    notes: str
    applied_at: datetime | None
    status: str
    refined_at: datetime | None

    model_config = {"from_attributes": True}


class JobUpdate(BaseModel):
    is_bookmarked: bool | None = None
    is_hidden: bool | None = None
    notes: str | None = None
    status: str | None = None
    applied_at: datetime | None = None


class RunResponse(BaseModel):
    id: int
    started_at: datetime
    completed_at: datetime | None
    status: str
    sites_scraped: int
    jobs_found: int
    jobs_matched: int
    jobs_new: int
    errors: list[dict] | None
    trigger: str

    model_config = {"from_attributes": True}
