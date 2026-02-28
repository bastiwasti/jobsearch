"""Scraper for Google job listings.

URL: https://www.google.com/about/careers/applications/jobs/results/
Pattern: Dynamic JS (SPA)
Docs: docs/sites/google.md
Filter approach: EXCLUDE only (no INCLUDE patterns at scrape time)
"""

from urllib.parse import urljoin

from rules.base import BaseSite
from rules.models import JobListing


class Google(BaseSite):
    name = "google"
    base_url = "https://www.google.com/about/careers/applications/"
    needs_browser = True

    # Configuration
    MAX_PAGES = 3
    DELAY_MS = 2000

    @property
    def search_url(self) -> str:
        return f"{self.base_url}jobs/results/?location=Germany&employment_type=FULL_TIME"

    async def fetch(self, page) -> str:
        html_parts = []

        for page_num in range(1, self.MAX_PAGES + 1):
            if page_num == 1:
                url = self.search_url
            else:
                url = f"{self.search_url}&page={page_num}"

            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(self.DELAY_MS)
            html = await page.content()
            html_parts.append(html)

        return "\n".join(html_parts)

    def parse(self, html: str) -> list[JobListing]:
        listings = []

        try:
            from bs4 import BeautifulSoup as BS

            soup = BS(html, "html5lib")
            job_cards = soup.select("li.lLd3Je")
            print(f"Found {len(job_cards)} total job cards in HTML")

            for i, card in enumerate(job_cards):
                try:
                    # Title
                    title_el = card.select_one("h3.QJPWVe")
                    title = title_el.get_text(strip=True) if title_el else ""
                    if not title:
                        continue

                    # URL (relative path)
                    link_el = card.select_one("a[href]")
                    href = link_el.get("href", "") if link_el else ""
                    if not href:
                        continue
                    url = urljoin(self.base_url, href)
                    # Strip query params from job URL (they're just search context)
                    url = url.split("?")[0]

                    # Location — multiple spans, deduplicate
                    loc_spans = card.select("span.r0wTof")
                    seen_locs = []
                    for span in loc_spans:
                        loc = span.get_text(strip=True).lstrip(";").strip()
                        if loc and loc not in seen_locs:
                            seen_locs.append(loc)
                    location = "; ".join(seen_locs)

                    # Experience level
                    exp_el = card.select_one(".VfPpkd-vQzf8d")
                    experience = exp_el.get_text(strip=True) if exp_el else ""

                    # Description snippet
                    desc_el = card.select_one(".VfPpkd-IqDDtd")
                    description = desc_el.get_text(strip=True) if desc_el else ""

                    listings.append(
                        JobListing(
                            title=title,
                            company="Google",
                            location=location,
                            url=url,
                            description=description,
                            job_type="full-time",
                            source_site=self.name,
                            raw_data={
                                "experience_level": experience,
                            },
                        )
                    )
                except Exception as e:
                    print(f"  Error processing card {i + 1}: {e}")
                    continue

        except Exception as e:
            print(f"Error parsing HTML: {e}")
            import traceback

            traceback.print_exc()

        return listings
