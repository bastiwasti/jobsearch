"""Shared utility functions for site scrapers.

Provides extraction helpers, browser interaction helpers, and job field
normalization. Individual site files import from here to stay simple.
"""

import re
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from bs4 import BeautifulSoup, Tag


# ---------------------------------------------------------------------------
# HTML extraction helpers
# ---------------------------------------------------------------------------

def make_soup(html: str, clean: bool = True) -> BeautifulSoup:
    """Parse HTML into BeautifulSoup, optionally stripping boilerplate tags."""
    soup = BeautifulSoup(html, "html.parser")
    if clean:
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
    return soup


def extract_text(element: Tag | None, selector: str, default: str = "") -> str:
    """Safe CSS selector text extraction from a BeautifulSoup element."""
    if element is None:
        return default
    found = element.select_one(selector)
    if found is None:
        return default
    return found.get_text(strip=True) or default


def extract_attr(element: Tag | None, selector: str, attr: str, default: str = "") -> str:
    """Safe CSS selector attribute extraction (href, src, etc.)."""
    if element is None:
        return default
    found = element.select_one(selector)
    if found is None:
        return default
    return found.get(attr, default) or default


def extract_all_text(element: Tag | None, selector: str) -> list[str]:
    """Extract text from all matching elements."""
    if element is None:
        return []
    return [el.get_text(strip=True) for el in element.select(selector) if el.get_text(strip=True)]


# ---------------------------------------------------------------------------
# Browser interaction helpers (async, for Playwright pages)
# ---------------------------------------------------------------------------

_COOKIE_SELECTORS = [
    "button[id*='accept']",
    "button[class*='accept']",
    "button[data-testid*='accept']",
    "button:has-text('Accept')",
    "button:has-text('Akzeptieren')",
    "button:has-text('Alle akzeptieren')",
    "button:has-text('Accept all')",
    "button:has-text('I agree')",
]


async def dismiss_cookie_banner(page, selectors: list[str] | None = None) -> None:
    """Try to click common cookie accept buttons. Fails silently."""
    for selector in (selectors or _COOKIE_SELECTORS):
        try:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=1000):
                await btn.click()
                return
        except Exception:
            continue


async def scroll_to_load(page, max_scrolls: int = 5, delay_ms: int = 1000) -> None:
    """Scroll page to trigger lazy loading / infinite scroll."""
    for _ in range(max_scrolls):
        prev_height = await page.evaluate("document.body.scrollHeight")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(delay_ms)
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == prev_height:
            break


async def click_load_more(page, selector: str, max_clicks: int = 5) -> None:
    """Click a 'Load More' button repeatedly until no more results."""
    for _ in range(max_clicks):
        try:
            btn = page.locator(selector).first
            if not await btn.is_visible(timeout=2000):
                break
            await btn.click()
            await page.wait_for_timeout(1000)
        except Exception:
            break


async def wait_for_content(page, selector: str, timeout_ms: int = 10000) -> None:
    """Wait for a specific element to appear on the page."""
    await page.wait_for_selector(selector, timeout=timeout_ms)


# ---------------------------------------------------------------------------
# Job field normalization
# ---------------------------------------------------------------------------

_SALARY_CLEANUP = re.compile(r"[^\d\-–,.kK€$£]")

def parse_salary(raw: str) -> str:
    """Best-effort salary normalization. Returns cleaned string or empty."""
    if not raw or not raw.strip():
        return ""
    return raw.strip()


_JOB_TYPE_MAP = {
    "full-time": re.compile(r"full[- ]?time|vollzeit|unbefristet", re.IGNORECASE),
    "part-time": re.compile(r"part[- ]?time|teilzeit", re.IGNORECASE),
    "contract": re.compile(r"contract|befristet|zeitarbeit", re.IGNORECASE),
    "internship": re.compile(r"internship|praktikum|werkstudent", re.IGNORECASE),
    "freelance": re.compile(r"freelance|freiberuf", re.IGNORECASE),
}

def classify_job_type(raw: str) -> str:
    """Classify into: full-time, part-time, contract, internship, freelance."""
    if not raw:
        return ""
    for job_type, pattern in _JOB_TYPE_MAP.items():
        if pattern.search(raw):
            return job_type
    return ""


_REMOTE_MAP = {
    "remote": re.compile(r"\bremote\b|home\s*office|100%\s*remote", re.IGNORECASE),
    "hybrid": re.compile(r"\bhybrid\b|teilweise\s*remote", re.IGNORECASE),
    "on-site": re.compile(r"\bon[- ]?site\b|vor\s*ort|präsenz", re.IGNORECASE),
}

def classify_remote(raw: str) -> str:
    """Classify into: remote, hybrid, on-site."""
    if not raw:
        return ""
    for remote_type, pattern in _REMOTE_MAP.items():
        if pattern.search(raw):
            return remote_type
    return ""


_RELATIVE_DATE_PATTERNS = [
    (re.compile(r"(\d+)\s*(?:day|tag)s?\s*ago|vor\s*(\d+)\s*tag", re.IGNORECASE), "days"),
    (re.compile(r"(\d+)\s*(?:week|woche)s?\s*ago|vor\s*(\d+)\s*woche", re.IGNORECASE), "weeks"),
    (re.compile(r"(\d+)\s*(?:hour|stunde)s?\s*ago|vor\s*(\d+)\s*stunde", re.IGNORECASE), "hours"),
    (re.compile(r"\b(?:today|heute)\b", re.IGNORECASE), "today"),
    (re.compile(r"\b(?:yesterday|gestern)\b", re.IGNORECASE), "yesterday"),
]

def parse_posted_date(raw: str) -> str:
    """Parse relative dates ('3 days ago', 'vor 2 Wochen') to ISO date string."""
    if not raw:
        return ""
    raw = raw.strip()

    # Try ISO format first
    iso_match = re.match(r"^\d{4}-\d{2}-\d{2}", raw)
    if iso_match:
        return iso_match.group(0)

    now = datetime.now()

    for pattern, unit in _RELATIVE_DATE_PATTERNS:
        match = pattern.search(raw)
        if not match:
            continue
        if unit == "today":
            return now.strftime("%Y-%m-%d")
        if unit == "yesterday":
            return (now - timedelta(days=1)).strftime("%Y-%m-%d")
        # Extract number from either group
        groups = match.groups()
        num = int(next(g for g in groups if g is not None))
        if unit == "days":
            return (now - timedelta(days=num)).strftime("%Y-%m-%d")
        if unit == "weeks":
            return (now - timedelta(weeks=num)).strftime("%Y-%m-%d")
        if unit == "hours":
            return (now - timedelta(hours=num)).strftime("%Y-%m-%d")

    return ""


def clean_description(html: str) -> str:
    """Strip HTML tags from job description, keep paragraph structure."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    # Replace <br>, <p>, <li> with newlines for structure
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for tag in soup.find_all(["p", "li"]):
        tag.insert_before("\n")
    text = soup.get_text()
    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# URL normalization / deduplication
# ---------------------------------------------------------------------------

_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "ref", "refId", "trackingId", "trk",
}

def normalize_url(url: str) -> str:
    """Strip tracking params and fragments for dedup comparison."""
    if not url:
        return ""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    cleaned = {k: v for k, v in params.items() if k not in _TRACKING_PARAMS}
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path.rstrip("/"),
        parsed.params,
        urlencode(cleaned, doseq=True) if cleaned else "",
        "",  # strip fragment
    ))
