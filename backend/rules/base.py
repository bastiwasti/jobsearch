"""Base class for all job site scrapers.

Each site is a single .py file in companies/ or aggregators/ that subclasses
BaseSite and implements fetch() and parse().
"""

from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from rules.models import JobListing
from rules import common


class BaseSite(ABC):
    """Base class for all job site scrapers.

    Subclass must define:
        name: str           - site identifier (e.g. "linkedin")
        base_url: str       - root URL for the site
        needs_browser: bool - whether Playwright is required (default True)

    Subclass must implement:
        fetch(page) -> str  - fetch HTML using Playwright page
        parse(html) -> list[JobListing] - extract listings from HTML
    """

    name: str = ""
    base_url: str = ""
    needs_browser: bool = True

    def __init__(self, search_config: dict | None = None):
        """Initialize with optional search configuration.

        Args:
            search_config: Search terms, location, filters. Keys depend on the site.
        """
        self.search_config = search_config or {}

    @property
    def search_url(self) -> str:
        """Build search URL from base_url + search_config.

        Override in subclass for sites with specific URL patterns.
        """
        return self.base_url

    # --- Subclass must implement ---

    @abstractmethod
    async def fetch(self, page) -> str:
        """Fetch page HTML using a Playwright page object.

        Args:
            page: Playwright Page instance from BrowserEngine.

        Returns:
            Raw HTML string of the page content.
        """
        pass

    @abstractmethod
    def parse(self, html: str) -> list[JobListing]:
        """Parse HTML into job listings.

        Should extract ALL listings from the page. Filtering happens
        centrally via rules/filters.py, not here.

        Args:
            html: Raw HTML string.

        Returns:
            List of JobListing objects.
        """
        pass

    # --- Common methods (inherited) ---

    def make_soup(self, html: str, clean: bool = True) -> BeautifulSoup:
        """Parse HTML into BeautifulSoup."""
        return common.make_soup(html, clean=clean)

    async def fetch_and_parse(self, page) -> tuple[list[JobListing], str]:
        """Main entry: fetch HTML then parse listings.

        Returns:
            Tuple of (listings, extraction_method) where method is 'css'.
        """
        html = await self.fetch(page)
        listings = self.parse(html)
        return listings, "css"

    async def dismiss_cookie_banner(self, page, selectors: list[str] | None = None) -> None:
        """Try to dismiss cookie consent banners."""
        await common.dismiss_cookie_banner(page, selectors)

    async def scroll_to_load(self, page, max_scrolls: int = 5, delay_ms: int = 1000) -> None:
        """Scroll page to trigger lazy loading."""
        await common.scroll_to_load(page, max_scrolls=max_scrolls, delay_ms=delay_ms)

    async def click_load_more(self, page, selector: str, max_clicks: int = 5) -> None:
        """Click 'Load More' button repeatedly."""
        await common.click_load_more(page, selector, max_clicks=max_clicks)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, url={self.base_url!r})"
