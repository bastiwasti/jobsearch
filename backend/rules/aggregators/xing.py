"""Scraper for XING job listings.

URL: https://www.xing.com/jobs/search
Pattern: Dynamic JS with AJAX pagination ("Mehr" button)
Docs: docs/sites/xing.md

Meta:
    - Multi-location: Searches 5 NRW cities + 1 remote (6 total searches)
    - Keywords: data, ai, analytics
    - Pagination: "Mehr" button (AJAX-based, adds 20 jobs per click)
    - Jobs per search: ~100 (5 clicks × 20 jobs)
    - Anti-bot: Moderate (2000ms delays recommended)
    - Parser: html.parser (works with concatenated HTML)
    - Test date: 2026-02-28
    - Status: Working, production-ready
    - Filter approach: EXCLUDE only (no INCLUDE patterns)
    - Detail pages: Skipped for now (listing data only)
"""

from urllib.parse import urljoin, quote

from rules.base import BaseSite
from rules.models import JobListing


class Xing(BaseSite):
    name = "xing"
    base_url = "https://www.xing.com/jobs/search"
    needs_browser = True

    # Configuration
    NRW_CITIES = ["Cologne", "Dusseldorf", "Dortmund", "Essen", "Bonn"]
    KEYWORDS = ["data", "ai", "analytics"]
    MAX_LOADS = 5
    DELAY_MS = 2000

    def __init__(self, search_config: dict | None = None):
        """Initialize with optional search configuration.

        Args:
            search_config: Search terms, location, filters. Keys depend on the site.
                         max_searches: Limit number of searches (for testing, default all)
        """
        self.search_config = search_config or {}
        self.max_searches = search_config.get('max_searches', None) if search_config else None

    @property
    def search_url(self) -> str:
        return self.base_url

    async def fetch(self, page) -> str:
        html_parts = []

        searches = [
            {"location": city} for city in self.NRW_CITIES
        ] + [{"workplace": "full-remote"}]

        search_count = 0
        for search in searches:
            if self.max_searches and search_count >= self.max_searches:
                print(f"Stopping at {search_count} searches (max_searches={self.max_searches})")
                break

            for keyword in self.KEYWORDS:
                if self.max_searches and search_count >= self.max_searches:
                    print(f"Stopping at {search_count} searches (max_searches={self.max_searches})")
                    break

                if "location" in search:
                    url = f"{self.base_url}?keywords={quote(keyword)}&location={quote(search['location'])}"
                else:
                    url = f"{self.base_url}?keywords={quote(keyword)}&workplace=full-remote"

                print(f"Search {search_count+1}: {keyword} {search.get('location', 'remote')}")
                await page.goto(url, wait_until='domcontentloaded')
                await page.wait_for_timeout(self.DELAY_MS)

                html_parts.append(await page.content())

                try:
                    for i in range(self.MAX_LOADS - 1):
                        mehr_btn = page.locator('button:has-text("Mehr")').first
                        await mehr_btn.wait_for(state='visible', timeout=3000)
                        await mehr_btn.click()
                        await page.wait_for_timeout(self.DELAY_MS)
                        html_parts.append(await page.content())
                except Exception:
                    break

                search_count += 1

        return "\n".join(html_parts)

    def parse(self, html: str) -> list[JobListing]:
        listings = []

        try:
            from bs4 import BeautifulSoup as BS
            soup = BS(html, "html.parser")

            job_cards = soup.select('[data-testid="job-search-result"]')
            print(f"Found {len(job_cards)} total job cards in HTML")

            for i, card in enumerate(job_cards):
                try:
                    title_el = card.select_one('h2, h3')
                    title = title_el.get_text(strip=True) if title_el else ""

                    link_el = card.select_one('a')
                    href = link_el.get('href', '') if link_el else ""

                    if not title or not href:
                        print(f"  Skipping card {i+1}: missing title or href")
                        continue

                    url = urljoin('https://www.xing.com', str(href))

                    card_text = card.get_text(separator=' ', strip=True)

                    company = ""
                    location = ""
                    salary = ""
                    posted_date = ""

                    lines = card_text.split('\n')
                    for j, line in enumerate(lines):
                        line = line.strip()
                        if not line:
                            continue
                        if any(city in line for city in self.NRW_CITIES) or 'Remote' in line or 'Berlin' in line or 'München' in line:
                            location = line
                        elif '€' in line and ('–' in line or '-' in line):
                            salary = line
                        elif 'ago' in line.lower() or 'vor' in line.lower() or 'gestern' in line.lower() or 'heute' in line.lower():
                            posted_date = line
                        elif j < len(lines) // 2 and not company:
                            company = line

                    listings.append(JobListing(
                        title=title,
                        company=company,
                        location=location,
                        url=url,
                        description="",
                        source_site=self.name,
                        raw_data={
                            "salary": salary,
                            "posted_date": posted_date,
                        }
                    ))
                except Exception as e:
                    print(f"  Error processing card {i+1}: {e}")
                    continue

        except Exception as e:
            print(f"Error parsing HTML: {e}")
            import traceback
            traceback.print_exc()

        return listings
