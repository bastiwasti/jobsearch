"""Research Amazon careers page structure."""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Test different Amazon careers URLs
        test_urls = [
            "https://www.amazon.jobs/en",
            "https://www.amazon.jobs/de",
            "https://www.amazon.jobs/en/search",
            "https://www.amazon.jobs/en/search?location=Germany",
            "https://www.amazon.jobs/de/search?location=Deutschland",
            "https://www.amazon.jobs/en/search?country=DE",
        ]
        
        for url in test_urls:
            print(f"\n=== Testing: {url} ===")
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"Error loading: {e}")
                continue
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for job listings
            job_cards = soup.select('[class*="job"]')  # Generic selector
            print(f"Found {len(job_cards)} job-like elements")
            
            # Look for specific Amazon job card structures
            amazon_cards = soup.select('[data-testid="job-card"]')
            if amazon_cards:
                print(f"Amazon job cards found: {len(amazon_cards)}")
                for i, card in enumerate(amazon_cards[:3]):
                    title = card.select_one('[class*="title"]')
                    location = card.select_one('[class*="location"]')
                    if title:
                        print(f"  {i+1}. Title: {title.get_text(strip=True)[:60]}")
                    if location:
                        print(f"      Location: {location.get_text(strip=True)}")
            
            await page.wait_for_timeout(500)
        
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
