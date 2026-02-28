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
        self.seen_urls = set()

    @property
    def search_url(self) -> str:
        return self.base_url

    async def fetch(self, page) -> str:
        html_parts = []

        searches = [
            {"location": city} for city in self.NRW_CITIES
        ] + [{"workplace": "full-remote"}]

        total_searches = len(searches) * len(self.KEYWORDS)
        print(f"Total searches planned: {total_searches} (max_searches={self.max_searches})")

        search_count = 0
        try:
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

                    print(f"Search {search_count+1}/{total_searches}: {keyword} {search.get('location', 'remote')}")
                    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(self.DELAY_MS)

                    html_parts.append(await page.content())

                    try:
                        for i in range(self.MAX_LOADS - 1):
                            mehr_btn = page.locator('button:has-text("Mehr")').first
                            await mehr_btn.wait_for(state='visible', timeout=5000)
                            await mehr_btn.evaluate('el => el.click()')
                            await page.wait_for_timeout(self.DELAY_MS)
                            html_parts.append(await page.content())
                            print(f"    Loaded page {i+2} for this search")
                    except Exception as e:
                        print(f"  Pagination error: {e}")
                        break

                    search_count += 1
        except Exception as e:
            print(f"ERROR in fetch: {e}")
            import traceback
            traceback.print_exc()

        print(f"Completed {search_count} searches")
        return "\n".join(html_parts)

    def parse(self, html: str) -> list[JobListing]:
        listings = []
        import re

        try:
            from bs4 import BeautifulSoup as BS
            soup = BS(html, "html.parser")

            job_cards = soup.select('[data-testid="job-search-result"]')
            print(f"Found {len(job_cards)} total job cards in HTML")

            for i, card in enumerate(job_cards):
                try:
                    if not card:
                        continue
                    title_el = card.select_one('h2')
                    title = title_el.get_text(strip=True) if title_el else ""

                    link_el = card.select_one('a')
                    href = link_el.get('href', '') if link_el else ""

                    if not title or not href:
                        print(f"  Skipping card {i+1}: missing title or href")
                        continue

                    url = urljoin('https://www.xing.com', str(href))

                    if url in self.seen_urls:
                        continue

                    self.seen_urls.add(url)

                    company = ""
                    location = ""
                    salary = ""
                    posted_date = ""

                    card_html = str(card)
                    company_match = re.search(r'(job-teaser-list-item-styles__Company[^>]*>)([^<]+)(</p>)', card_html)
                    if company_match:
                        company = company_match.group(2).strip()

                    location_match = re.search(r'<p[^>]*?data-xds="BodyCopy"[^>]*?>([^<]+)</p>', card_html)
                    if location_match:
                        location = location_match.group(1).strip()
                    else:
                        for city in self.NRW_CITIES:
                            if re.search(r'\b' + re.escape(city) + r'\b', card_html):
                                location = city
                                break

                    salary_match = re.search(r'€[^<]*>€[^<]*<[^>]*([€0-9.,\s–\s]+[€0-9.,\s]+)', card_html)
                    if salary_match:
                        salary = salary_match.group(1).replace(' ', ' ').strip()

                    posted_date_match = re.search(r'publication-date[^>]*>([^<]+)</p>', card_html)
                    if posted_date_match:
                        posted_date = posted_date_match.group(1).strip()

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

