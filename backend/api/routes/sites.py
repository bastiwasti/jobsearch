"""Registered site endpoints."""

from fastapi import APIRouter

from rules.registry import get_registry

router = APIRouter()


@router.get("/sites")
def list_sites():
    registry = get_registry()
    return [
        {
            "name": name,
            "base_url": cls.base_url,
            "needs_browser": cls.needs_browser,
            "category": "aggregator" if ".aggregators." in cls.__module__ else "company",
        }
        for name, cls in sorted(registry.items())
    ]
