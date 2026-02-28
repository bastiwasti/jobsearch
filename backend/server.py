"""FastAPI server entry point.

Run with: uvicorn server:app --reload --port 8000
"""

from api.app import app  # noqa: F401
