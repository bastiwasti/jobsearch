# Google

## URL
https://www.google.com/about/careers/applications/jobs/results/?location=Germany&employment_type=FULL_TIME

## Status
Working

## Approach
Dynamic JS - requires Playwright for JavaScript rendering (SPA, no server-side HTML)

## Configuration
- **Location Strategy**: local (pre-filter `?location=Germany`)
- **Pagination Limit**: max_pages=3 (45 total jobs in Germany, 20 per page)
- **Rate Limiting**: delay_ms=2000

## Page Structure
Job listings rendered client-side via JavaScript SPA. Each job card is `<li class="lLd3Je">` inside a list. 20 cards per page.

## Job Card Fields

| Field | Selector / Path | Notes |
|-------|----------------|-------|
| title | `h3.QJPWVe` | Job title text |
| company | `.RP7SMd` | Contains "corporate_fareGoogle" - strip icon text |
| location | `span.r0wTof` | Multiple spans per card (multi-location), deduplicate |
| url | `a[href]` | Relative paths like `jobs/results/{id}-{slug}?...`, need urljoin |
| description | `.VfPpkd-IqDDtd` | Short snippet/summary |
| experience | `.VfPpkd-vQzf8d` | Level: Early, Mid, Advanced |
| salary | N/A | Not available on listing page |
| job_type | N/A | Pre-filtered to FULL_TIME via URL |
| remote | N/A | Not shown on listing page |
| posted_date | N/A | Not available on listing page |

## Pagination
URL-based: `&page=N` parameter, 20 results per page.
VERIFIED: page 1 and page 2 have different content: YES (0 title overlap)
Page 1: 20 cards, Page 2: 20 cards, Page 3: 5 cards (45 total for Germany)

## Challenges
- 100% client-side rendered SPA — needs Playwright
- No salary, remote, or posted_date info on listing cards
- Location spans are duplicated in DOM (same location appears twice) — need dedup
- Company text includes Material icon text "corporate_fare" — need to strip
- Job URLs are relative — need urljoin with base URL
- No dedicated data/AI category filter — use global filters to select relevant roles

## Sample Data

1. Customer Engineer, Platform, Discrete Manufacturing, DACH (German)
   - Location: Munich, Germany; Frankfurt am Main, Germany
   - Experience: Mid
   - URL: jobs/results/113483160762622662-customer-engineer-...

2. AI Sales Specialist, Google Cloud
   - Location: Munich, Germany; Zürich, Switzerland
   - Experience: Advanced

3. Staff Software Engineer, Agent Foundations
   - Location: Munich, Germany
   - Experience: Advanced

---
## Implementation
- File: `rules/companies/google.py`
- Class: `Google`
- Pattern: Dynamic JS with Playwright
- Date: 2026-02-28
- Config:
  - Location Strategy: local (`?location=Germany`)
  - Pagination Limit: 3 pages
  - Rate Limiting: 2000ms delay

## Test Results

- Jobs parsed: 45
- Jobs matched EXCLUDE filters: 41/45 (4 excluded: Legal Trainee x3, Product Manager I)
- Jobs stored (new): 41

## Learnings

- Scraper works correctly — all 45 jobs parsed successfully from 3 pages
- Location spans appear duplicated in the DOM (each location shows twice) — dedup logic handles this
- Company name is always "Google" — hardcoded rather than parsing from DOM (which includes icon text "corporate_fare")
- Job URLs contain query params from the search context — strip them for cleaner dedup
- No remote indicator on listing cards means remote Google jobs won't be detected at scrape time (would need detail page scraping)
- html5lib parser required for multi-page HTML concatenation
- Google careers page is region-neutral — `?location=Germany` works without region-specific URLs (unlike Apple which needs `de-de`)
