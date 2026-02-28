"""Scrape run endpoints."""

from fastapi import APIRouter
from sqlalchemy import select

from api.schemas import RunResponse
from db.connection import get_session
from db.models import ScrapeRun

router = APIRouter()


@router.get("/runs", response_model=list[RunResponse])
def list_runs(limit: int = 20):
    session = get_session()
    query = select(ScrapeRun).order_by(ScrapeRun.id.desc()).limit(limit)
    runs = session.scalars(query).all()
    session.close()
    return runs
