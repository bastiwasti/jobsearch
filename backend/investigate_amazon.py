"""Deep investigation of Amazon job search structure."""
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("=== Loading Amazon search page ===")
        await page.goto("https://www.amazon.jobs/en/search", wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(5000)
        
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find job cards - try different selectors
        selectors = [
            'a[href*="/jobs/"]',
            '[class*="job"]',
            '[data-testid]',
            '[data-job]',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            print(f"\nSelector '{selector}': {len(elements)} elements")
            
            if len(elements) > 100:  # Found actual job listings
                print("\nSample jobs:")
                for i, el in enumerate(elements[:5]):
                    href = el.get('href', '')
                    text = el.get_text(strip=True)[:80]
                    print(f"  {i+1}. {text}")
                    if href:
                        print(f"      URL: {href[:80]}")
                break
        
        # Look for pagination
        print("\n\n=== Pagination ===")
        pagination = soup.select('nav, .pagination, [class*="page"]')
        print(f"Pagination elements found: {len(pagination)}")
        for pag in pagination:
            print(f"  {pag.get('class', '')}: {pag.get_text(strip=True)[:100]}")
        
        # Check for location filters in the page
        print("\n\n=== Location Filter Options ===")
        location_inputs = soup.select('input[name*="location"], select[name*="location"], [class*="location-filter"]')
        print(f"Location input elements: {len(location_inputs)}")
        for i, loc in enumerate(location_inputs[:3]):
            print(f"  {i+1}. {str(loc)[:100]}")
        
        # Save HTML for inspection
        with open('/tmp/amazon_search.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("\nSaved HTML to /tmp/amazon_search.html")
        
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
