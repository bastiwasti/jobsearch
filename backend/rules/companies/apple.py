"""Scraper for Apple job listings.

URL: https://jobs.apple.com/en-us/search
Pattern: Dynamic JS
Docs: docs/sites/apple.md
Filter approach: EXCLUDE only (no INCLUDE patterns)
"""

from urllib.parse import urljoin

from rules.base import BaseSite
from rules.models import JobListing
from rules.common import extract_text, extract_attr

class Apple(BaseSite):
    name = "apple"
    base_url = "https://jobs.apple.com/de-de/search"
    needs_browser = True

    # Configuration
    MAX_PAGES = 3
    DELAY_MS = 1500

    @property
    def search_url(self) -> str:
        return f"{self.base_url}?location=germany-DEU&sort=newest"

    async def fetch(self, page) -> str:
        html_parts = []
        
        for page_num in range(1, self.MAX_PAGES + 1):
            # Build URL for pagination
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
            
            job_cards = soup.select('li.rc-accordion-item')
            print(f"Found {len(job_cards)} total job cards in HTML")
            
            # Process cards with individual error handling
            for i, card in enumerate(job_cards):
                try:
                    title_link = card.select_one('a.link-inline.t-intro.word-wrap-break-word.more')
                    title = title_link.get_text(strip=True) if title_link else ""
                    href = title_link.get('href', '') if title_link else ""
                    
                    if not title or not href:
                        print(f"  Skipping card {i+1}: missing title or href")
                        continue
                    
                    url = urljoin(self.base_url, str(href))
                    
                    team = card.select_one('.team-name.mt-0')
                    team_text = team.get_text(strip=True) if team else ""
                    
                    posted = card.select_one('.job-posted-date')
                    posted_date = posted.get_text(strip=True) if posted else ""
                    
                    loc = card.select_one('.table--advanced-search__location-sub')
                    location = loc.get_text(strip=True) if loc else ""
                    
                    desc = card.select_one('p.text-align-start.pb-20.pt-10.column.large-12 span')
                    description = desc.get_text(strip=True) if desc else ""
                    
                    role_number = ""
                    weekly_hours = ""
                    for span in card.find_all('span'):
                        span_id = str(span.get('id', ''))
                        if 'role-number' in span_id:
                            role_number = span.get_text(strip=True)
                        elif 'weekly-hours' in span_id:
                            weekly_hours = span.get_text(strip=True)
                    
                    listings.append(JobListing(
                        title=title,
                        company="Apple",
                        location=location,
                        url=url,
                        description=description,
                        source_site=self.name,
                        raw_data={
                            "team": team_text,
                            "role_number": role_number,
                            "weekly_hours": weekly_hours,
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
