"""Auto-discovery registry for job site scrapers.

Scans rules/companies/*.py and rules/aggregators/*.py for BaseSite subclasses,
builds a name → class mapping.
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Type

from rules.base import BaseSite


_registry: dict[str, Type[BaseSite]] | None = None


def _discover_sites() -> dict[str, Type[BaseSite]]:
    """Scan companies/ and aggregators/ for BaseSite subclasses."""
    sites = {}
    rules_dir = Path(__file__).parent

    for category in ("companies", "aggregators"):
        package_dir = rules_dir / category
        if not package_dir.is_dir():
            continue

        package_path = f"rules.{category}"

        for _importer, module_name, _is_pkg in pkgutil.iter_modules([str(package_dir)]):
            if module_name.startswith("_"):
                continue

            try:
                module = importlib.import_module(f"{package_path}.{module_name}")
            except Exception as e:
                print(f"Warning: Failed to import {package_path}.{module_name}: {e}")
                continue

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseSite)
                    and attr is not BaseSite
                    and getattr(attr, "name", "")
                    and not getattr(attr, "disabled", False)
                ):
                    sites[attr.name] = attr

    return sites


def get_registry() -> dict[str, Type[BaseSite]]:
    """Get the site registry, discovering on first call."""
    global _registry
    if _registry is None:
        _registry = _discover_sites()
    return _registry


def get_site(name: str, search_config: dict | None = None) -> BaseSite:
    """Get a site instance by name."""
    registry = get_registry()
    if name not in registry:
        available = ", ".join(sorted(registry.keys()))
        raise ValueError(f"Unknown site: {name!r}. Available: {available}")
    return registry[name](search_config=search_config)


def get_all_sites(search_config: dict | None = None) -> list[BaseSite]:
    """Get instances of all registered sites."""
    registry = get_registry()
    return [cls(search_config=search_config) for cls in registry.values()]


def list_site_names() -> list[str]:
    """List all registered site names."""
    return sorted(get_registry().keys())
