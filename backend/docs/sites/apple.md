# Apple

## URL
https://jobs.apple.com/de-de/search?location=germany-DEU&sort=newest

## Status
✅ Working - Successfully scrapes 60 listings from 3 pages

## Approach
Dynamic JS - requires Playwright for JavaScript rendering

## 🔑 Critical Finding: URL Format

**Initial Approach (WRONG)**:
- Tested: `https://jobs.apple.com/en-us/search?location=Germany`
- Result: 5 jobs, empty locations, filter not working
- Tested: `https://jobs.apple.com/en-us/search?search=Germany`
- Result: 24 jobs, keyword search not location

**Correct Approach (Working)**:
- User suggested: `https://jobs.apple.com/de-de/search?location=germany-DEU`
- Result: 25 jobs, German-specific locations ("Mehrere Standorte in Deutschland")
- **Key insight**: Region (de-de) + country code (germany-DEU) both required

**Lesson**: Always test different URL formats for location filtering:
- Region-specific URLs (de-de, en-us, fr-fr)
- Country codes (DEU, GBR, AUT, CHE)
- Verify by fetching 2 different URLs and confirming results differ

## Configuration
- **Location Strategy**: local (German region `de-de` with country code `germany-DEU`)
- **Pagination Limit**: 3 pages (pre-filtered to Germany, fewer results)
- **Rate Limiting**: 1500ms delay between requests
- **Filter Approach**: EXCLUDE only (no INCLUDE patterns - saves broader dataset)

## Page Structure
Job listings loaded via JavaScript. Each job card is in `<li data-core-accordion-item>` within `<ul id="search-job-list">`.

## Job Card Fields
| Field | Selector / Path | Notes |
|-------|----------------|-------|
| title | `a.link-inline.t-intro.word-wrap-break-word.more` | |
| company | Apple | Always Apple |
| location | `.table--advanced-search__location-sub` | |
| url | `a[aria-label*="details"] href` | Relative paths, need urljoin |
| description | `p.text-align-start.pb-20.pt-10 span` | Preview text only |
| team | `.team-name.mt-0` | Team/department name |
| role_number | `span[id*="role-number"]` | |
| weekly_hours | `span[id*="weekly-hours"]` | |
| posted_date | `.job-posted-date` | |

## Pagination
URL-based pagination: `?location=germany-DEU&sort=newest&page=N` for page number
{VERIFIED: page 1 and page 2 have different content? YES}

## Challenges
- Heavily JavaScript-rendered (needs Playwright)
- Cookie banners may block content
- No salary info available
- No job_type/remote info available
- EN-US region location filtering doesn't work reliably
- Must use German region (`de-de`) with country code (`germany-DEU`) for proper location filtering

## Challenges
- Heavily JavaScript-rendered (needs Playwright)
- Cookie banners may block content
- No salary info available
- No job_type/remote info available

## Sample Data
- Multiple jobs at "Mehrere Standorte in Deutschland" (Various locations in Germany)
- German region-specific job postings

---
## Implementation
- File: `rules/companies/apple.py`
- Class: `Apple`
- Pattern: Dynamic JS with Playwright
- Date: 2026-02-28
- Config:
  - Location Strategy: local (German region `de-de` with country code `germany-DEU`)
  - Pagination Limit: 3 pages
  - Rate Limiting: 1500ms delay between requests

## Test Results

- Jobs parsed: 60 (75 cards, 15 skipped as UI elements)
- Jobs matched EXCLUDE filters: 59/60 (1 excluded: "Junior RF Applications Engineer")
- Jobs stored (new): 59

## Learnings
- Job listings use `<li data-core-accordion-item>` as container
- Multi-page HTML concatenation requires html5lib parser (more lenient)
- Individual error handling per card prevents single failures from stopping entire parse
- No salary, job_type, or remote information available on listing page
- Pagination uses URL parameter `?location=germany-DEU&sort=newest&page=N`
- EN-US region location filtering doesn't work reliably
- German region (`de-de`) with country code (`germany-DEU`) works for location filtering
- Some cards skipped (~15/75) due to missing title links (expected, duplicate/UI elements)
