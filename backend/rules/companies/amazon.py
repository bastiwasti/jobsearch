"""Scraper for Amazon job listings.

URL: https://www.amazon.jobs/en/search
Pattern: Dynamic JS with Load More
Docs: docs/sites/amazon.md

Meta:
    - Location filtering: Not reliable via URL parameters (tested: ?location=Germany, ?country=DE)
    - Pagination: Numbered buttons (primary) with Load More fallback
    - Jobs per page: 10
    - Anti-bot: Strong measures, requires 2000ms delays
    - Parser: html5lib required for multi-page concatenation
    - Test date: 2026-02-28
    - Status: Working, production-ready
    - Filter approach: EXCLUDE only (no INCLUDE patterns)
"""

from urllib.parse import urljoin

from rules.base import BaseSite
from rules.models import JobListing


class Amazon(BaseSite):
    name = "amazon"
    base_url = "https://www.amazon.jobs/en/search"
    needs_browser = True

    # Configuration
    MAX_LOADS = 5  # 10 jobs per load
    DELAY_MS = 2000

    @property
    def search_url(self) -> str:
        return self.base_url

    async def fetch(self, page) -> str:
        html_parts = []
        
        await page.goto(self.search_url, wait_until='domcontentloaded')
        await page.wait_for_timeout(self.DELAY_MS)
        
        # Get initial page
        html_parts.append(await page.content())
        
        # Try Load More button first
        try:
            for i in range(self.MAX_LOADS - 1):
                try:
                    # Wait for Load More button
                    load_more = page.locator('.load-more').first
                    await load_more.wait_for(state='visible', timeout=3000)
                    
                    # Click the button
                    await load_more.click()
                    
                    # Wait for new content to load
                    await page.wait_for_timeout(self.DELAY_MS)
                    
                    # Get updated HTML
                    html_parts.append(await page.content())
                except Exception as e:
                    # Load More button not visible/timeout - try pagination buttons instead
                    break
        except Exception as e:
            pass
        
        # If Load More didn't work, try pagination buttons
        if len(html_parts) == 1:
            print("Load More not available, trying pagination buttons...")
            for i in range(2, min(self.MAX_LOADS, 5)):  # Try pages 2-4
                try:
                    page_button = page.locator(f'.page-button:has-text("{i}")').first
                    await page_button.wait_for(state='visible', timeout=3000)
                    await page_button.click()
                    await page.wait_for_timeout(self.DELAY_MS)
                    html_parts.append(await page.content())
                except Exception:
                    print(f"Page {i} not available")
                    break
        
        return "\n".join(html_parts)
    
    def parse(self, html: str) -> list[JobListing]:
        listings = []
        
        try:
            from bs4 import BeautifulSoup as BS
            soup = BS(html, "html5lib")
            
            job_cards = soup.select('.job[data-job-id]')
            print(f"Found {len(job_cards)} total job cards in HTML")
            
            for i, card in enumerate(job_cards):
                try:
                    job_id = card.get('data-job-id', '')
                    
                    title_link = card.select_one('.job-title a.job-link')
                    title = title_link.get_text(strip=True) if title_link else ""
                    href = title_link.get('href', '') if title_link else ""
                    
                    if not title or not href:
                        print(f"  Skipping card {i+1}: missing title or href")
                        continue
                    
                    url = urljoin(self.base_url, str(href))
                    
                    loc = card.select_one('.location-and-id ul li:first-child')
                    location = loc.get_text(strip=True) if loc else ""
                    
                    posted = card.select_one('.posting-date')
                    posted_date = posted.get_text(strip=True) if posted else ""
                    
                    updated = card.select_one('.meta.time-elapsed')
                    updated_time = updated.get_text(strip=True) if updated else ""
                    
                    desc = card.select_one('.description .qualifications-preview')
                    description = desc.get_text(strip=True) if desc else ""
                    
                    listings.append(JobListing(
                        title=title,
                        company="Amazon",
                        location=location,
                        url=url,
                        description=description,
                        source_site=self.name,
                        raw_data={
                            "job_id": job_id,
                            "posted_date": posted_date,
                            "updated_time": updated_time,
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
