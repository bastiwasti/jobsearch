"""FastAPI application setup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, jobs, runs, sites


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="JobSearch API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(sites.router, prefix="/api")
