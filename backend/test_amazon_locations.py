"""Test Amazon location filtering."""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Test different location approaches
        test_cases = [
            {
                "name": "Base search (no filter)",
                "url": "https://www.amazon.jobs/en/search"
            },
            {
                "name": "URL with location=Germany",
                "url": "https://www.amazon.jobs/en/search?location=Germany"
            },
            {
                "name": "URL with country=DE",
                "url": "https://www.amazon.jobs/en/search?country=DE"
            },
            {
                "name": "German region /de/search",
                "url": "https://www.amazon.jobs/de/search"
            },
            {
                "name": "German region with location",
                "url": "https://www.amazon.jobs/de/search?location=Deutschland"
            },
        ]
        
        for test in test_cases:
            print(f"\n=== {test['name']} ===")
            try:
                await page.goto(test['url'], wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(3000)
                
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Count jobs
                jobs = soup.select('.job[data-job-id]')
                print(f"Jobs found: {len(jobs)}")
                
                if jobs:
                    # Check first job's location
                    first_job = jobs[0]
                    loc = first_job.select_one('.location-and-id ul li:first-child')
                    if loc:
                        print(f"First location: {loc.get_text(strip=True)}")
            except Exception as e:
                print(f"Error: {e}")
            
            await page.wait_for_timeout(1000)
        
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
