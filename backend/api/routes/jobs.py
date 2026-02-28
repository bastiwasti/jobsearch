"""Job listing endpoints."""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from api.schemas import JobResponse, JobUpdate
from db.connection import get_session
from db.models import Job

router = APIRouter()


@router.get("/jobs", response_model=list[JobResponse])
def list_jobs(
    source_site: str | None = None,
    status: str | None = None,
    is_bookmarked: bool | None = None,
    search: str | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
):
    session = get_session()
    query = select(Job).where(Job.is_hidden == False)

    if source_site:
        query = query.where(Job.source_site == source_site)
    if status:
        query = query.where(Job.status == status)
    if is_bookmarked is not None:
        query = query.where(Job.is_bookmarked == is_bookmarked)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            Job.title.ilike(pattern) | Job.company.ilike(pattern) | Job.description.ilike(pattern)
        )

    query = query.order_by(Job.created_at.desc()).offset(offset).limit(limit)
    jobs = session.scalars(query).all()
    session.close()
    return jobs


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int):
    session = get_session()
    job = session.get(Job, job_id)
    session.close()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/jobs/{job_id}", response_model=JobResponse)
def update_job(job_id: int, update: JobUpdate):
    session = get_session()
    job = session.get(Job, job_id)
    if not job:
        session.close()
        raise HTTPException(status_code=404, detail="Job not found")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(job, field, value)

    session.commit()
    session.refresh(job)
    session.close()
    return job
