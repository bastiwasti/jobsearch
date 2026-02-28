"""Shared Playwright browser instance for scrape runs.

Keeps one Chromium browser alive across all sites in a run,
creating isolated pages per site. Use as async context manager:

    async with BrowserEngine() as engine:
        page = await engine.new_page()
        await page.goto(url)
        html = await page.content()
        await page.close()
"""

from playwright.async_api import async_playwright, Browser, Page, Playwright

from config import PLAYWRIGHT_HEADLESS


class BrowserEngine:
    """Manages a shared Playwright browser for the duration of a scrape run."""

    def __init__(self):
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        """Launch Chromium browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=PLAYWRIGHT_HEADLESS,
        )

    async def new_page(self) -> Page:
        """Create a fresh page with isolated browser context."""
        if self._browser is None:
            raise RuntimeError("BrowserEngine not started. Call start() or use as context manager.")
        context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
        )
        return await context.new_page()

    async def stop(self) -> None:
        """Close browser and Playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def __aenter__(self) -> "BrowserEngine":
        await self.start()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.stop()
