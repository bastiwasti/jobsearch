# Amazon

## URL
https://www.amazon.jobs/en/search

## Status
❌ **SKIPPED** - Requires Google login to access job listings

## Reason for Skipping
Amazon.jobs now requires authenticated access (Google OAuth) to view job listings. Unauthenticated requests receive a placeholder result set (10 generic US jobs) regardless of URL parameters or language settings.

## Investigation (2026-02-28)

### Findings:
- Unauthenticated access returns placeholder jobs only (10 generic US roles)
- Germany jobs exist (~1% of listings) but are only visible when logged in
- URL parameters (`?location=Germany`, `?country=DE`) have no effect without authentication
- German language page (`/de/search`) returns same placeholder results as English
- Location filtering is only available to authenticated users

### Auth Requirements:
- Google OAuth login required
- Account creation needed before access
- 2FA typically enabled on accounts
- Session tokens would need to be stored/refreshed

### Alternatives for Amazon Germany:
- **LinkedIn Jobs** - Search for "Amazon" + "Germany"
- **StepStone** - Aggregates Amazon Germany postings
- **Indeed Germany** - Aggregates Amazon Germany postings
- **AWS Careers** - Separate site may have different auth requirements

### Technical Challenges:
1. OAuth complexity - Interactive approval flow required
2. 2FA - Cannot be automated without security risks
3. Session management - Cookie/token storage and refresh
4. Anti-bot detection - Amazon monitors automated logins
5. Security - Storing Google credentials is unsafe

## Approach
Dynamic JS - requires Playwright for JavaScript rendering

## Configuration
- **Location Strategy**: global (URL location parameters don't work reliably)
- **Pagination Limit**: 5 loads (pagination buttons 1-4, 10 jobs/load)
- **Rate Limiting**: 2000ms delay between requests (Amazon has strong anti-bot)
- **Filter Approach**: EXCLUDE only (no INCLUDE patterns - saves broader dataset)

## Page Structure
Job listings use numbered pagination with button clicks. Job cards are in `.job` elements with `data-job-id` attribute.

## Job Card Fields
| Field | Selector / Path | Notes |
|-------|----------------|-------|
| job_id | `.job[data-job-id]` attribute | Primary identifier |
| title | `.job-title a.job-link` | Job title |
| url | `.job-title a.job-link` href attribute | /en/jobs/{job_id}/{slug} |
| location | `.location-and-id ul li:first-child` | City, State, Country |
| posted_date | `.posting-date` | Posted date |
| updated_time | `.meta.time-elapsed` | "Updated about X hours ago" |
| description | `.description .qualifications-preview` | Preview text |
| read_more | `.description a.read-more` | Link to full description |

## Pagination
- **Type**: Numbered pagination buttons (1, 2, 3, 4, ...)
- **Button selector**: `.page-button:has-text("{N}")` where N is page number
- **Jobs per page**: 10 jobs
- **Fallback**: "Load More" button (`.load-more`) - not visible in initial tests

## Challenges
- **❌ Login Required** - Must authenticate with Google OAuth to see real job listings
- Heavily JavaScript-rendered (needs Playwright)
- Location filtering via URL doesn't work without authentication
- Strong anti-bot measures (rate limiting)
- No salary info available
- No job_type/remote info available
- Team/Category info not visible in job cards (may need detail page)
- "Load More" button not always visible - pagination buttons used instead

## Sample Data
- Engineering Operations Technician (Sparks, NV, USA)
- Software Development Engineer (Sparks, NV, USA)
- Data Engineer (Sparks, NV, USA)

---
## Implementation
- File: `rules/companies/amazon.py`
- Class: `Amazon`
- Pattern: Dynamic JS with Playwright
- Date: 2026-02-28
- Config:
  - Location Strategy: global (URL location parameters don't work)
  - Pagination Limit: 4-5 pages
  - Rate Limiting: 2000ms delay between requests

## Test Results
- Jobs parsed: 40 listings (4 pages, 10 per page)
- Jobs matched EXCLUDE filters: 40/40 (0 excluded)
- Jobs stored (new): 40
- Extraction method: css with html5lib parser
- Pagination: Numbered buttons working correctly (Load More fallback not used)
- Note: Global strategy means worldwide jobs are stored; INCLUDE/LOCAL filtering applied later

## Learnings
- Job listings use `.job[data-job-id]` as container
- Pagination via numbered buttons (1, 2, 3, ...) not "Load More"
- "Load More" button exists but not visible in initial page load
- Location URL parameters (`?location=Germany`, `?country=DE`) don't filter results
- All jobs default to Sparks, NV, USA regardless of URL
- With EXCLUDE-only filtering, all non-junior/trainee jobs are saved for later refinement

---
## Meta

### Key Implementation Patterns

**Pagination Strategy**: Amazon uses numbered pagination buttons (`.page-button:has-text("{N}")`) as primary mechanism, with a hidden "Load More" button (`.load-more`) as fallback. This differs from typical "Load More" infinite scroll pattern.

**Location Filtering**: Unlike Apple where `de-de?location=germany-DEU` works, Amazon's location filters via URL parameters (`?location=Germany`, `?country=DE`) are unreliable or ineffective. All results default to US locations regardless of URL parameters.

**Anti-Bot Handling**: Amazon has strong anti-bot measures. Requires:
- Longer delays between requests (2000ms vs 1500ms)
- Explicit waiting for button visibility before clicking
- Proper DOM content loaded state (`domcontentloaded` not `networkidle`)

### Common Pitfalls Encountered

1. **Assuming "Load More" button is visible**
   - **Issue**: `.load-more` button exists in HTML but isn't initially visible
   - **Fix**: Added fallback to numbered pagination buttons with try/except

2. **Trusting URL location parameters without verification**
   - **Issue**: Multiple location URL formats tested, none filtered correctly
   - **Fix**: Documented failure modes, chose global strategy with LOCAL_PATTERNS reliance

3. **Using html.parser for concatenated HTML**
   - **Issue**: Multiple pages with duplicate DOCTYPE tags break html.parser
   - **Fix**: Used html5lib parser (more lenient)

### Best Practices Applied

1. **Thorough URL testing**: Tested multiple location URL formats before committing to implementation
2. **Fallback mechanisms**: Implemented dual pagination strategy (primary buttons + fallback "Load More")
3. **Per-card error handling**: Individual try/except prevents single bad card from stopping entire scrape
4. **Conservative rate limiting**: Longer delays (2000ms) due to Amazon's anti-bot measures
5. **Parser choice**: html5lib for multi-page HTML concatenation reliability
- Thorough URL testing is critical before implementation (follows refined guide)

## Skip Decision

**Date:** 2026-02-28
**Reason:** Authentication requirement makes scraping impractical and unsafe
**Action:** Scraper disabled, job listing acquisition requires manual login or use of alternative job boards

**Re-enabled if:** Amazon.jobs offers public API access or removes authentication requirement for job listings
