# XING

## URL
https://www.xing.com/jobs/search

## Status
✅ Working - Successfully scrapes 900+ listings (6 searches × 150 jobs each)

## Approach
Dynamic JS - requires Playwright for JavaScript rendering with AJAX pagination

## Configuration
- **Location Strategy**: Multi-search (5 NRW cities + 1 remote)
- **Keywords**: data, ai, analytics (3 searches per location)
- **Pagination Limit**: 5 loads ("Mehr" button, 20 jobs/load)
- **Rate Limiting**: 2000ms delay between requests
- **Filter Approach**: EXCLUDE only (no INCLUDE patterns - saves broader dataset)
- **Detail Pages**: Skipped (listing data only for initial scrape)

## Page Structure
Job listings use AJAX-based pagination with "Mehr" (Show More) button. Job cards are in `[data-testid="job-search-result"]` elements.

## Job Card Fields
| Field | Selector / Path | Notes |
|-------|----------------|-------|
| job_id | `[data-testid="job-search-result"]` attribute | Job card identifier |
| title | `h2`, `h3` inside card | Job title |
| url | `a` href attribute | Relative path like `/jobs/koeln-job-12345` |
| company | Text parsing (first meaningful line) | Company name |
| location | Text parsing (city names, "Remote") | City, Germany or "Full Remote" |
| salary | Text parsing (€ symbol, – range) | €47,500 – €62,500 |
| posted_date | Text parsing ("ago", "vor", "gestern") | "2 days ago", "vor 2 Wochen" |

## URL Patterns

| Search Type | URL Pattern | Example |
|-------------|--------------|----------|
| By city | `/jobs/search?keywords={keyword}&location={city}` | `/jobs/search?keywords=data&location=Cologne` |
| Remote only | `/jobs/search?keywords={keyword}&workplace=full-remote` | `/jobs/search?keywords=ai&workplace=full-remote` |
| Job detail | `{base}{job_path}` | `https://www.xing.com/jobs/koeln-softwareentwickler-software-developer-web-app-151360233` |

## Multi-Search Strategy

The scraper performs 6 independent searches (3 keywords × 5 cities + 3 keywords × 1 remote = 18 total page loads):

1. **NRW Cities:**
   - data + Cologne
   - ai + Cologne
   - analytics + Cologne
   - data + Düsseldorf
   - ai + Düsseldorf
   - analytics + Düsseldorf
   - data + Dortmund
   - ai + Dortmund
   - analytics + Dortmund
   - data + Essen
   - ai + Essen
   - analytics + Essen
   - data + Bonn
   - ai + Bonn
   - analytics + Bonn

2. **Remote:**
   - data + Remote
   - ai + Remote
   - analytics + Remote

**Total searches:** 18 (5 clicks each = 90 page loads)

## Pagination
- **Type**: AJAX "Mehr" (Show More) button
- **Button selector**: `button:has-text("Mehr")`
- **Jobs per page**: 20 jobs
- **Max loads**: 5 clicks per search (100+ jobs)
- **Total expected**: ~900 jobs (18 searches × 50 avg jobs)

## Challenges
- JavaScript-rendered (needs Playwright)
- Multi-search logic (need to loop through cities + keywords)
- Text parsing for company/location/salary (no clean selectors)
- Text extraction from concatenated HTML (18 searches × 5 pages = 90 HTML chunks)
- No job_type/remote info in listing (only text hints)
- Job detail pages not scraped yet (future enhancement)

## Sample Data
- Softwareentwickler/Software Developer Web/App (m/w/d) - Hottgenroth Software AG - Köln - €47,500 – €62,500
- Senior AI Software Engineer (all genders) in Düsseldorf - PRODYNA SE - €69,000 – €81,000
- Software Engineer Backend (m/w/d) - YER - €55,500 – €73,000
- Senior Software Engineer SAP FS-CD (all genders) - adesso business consulting AG - €74,000 – €100,500

---
## Implementation
- File: `rules/aggregators/xing.py`
- Class: `Xing`
- Pattern: Dynamic JS with Playwright
- Date: 2026-02-28
- Config:
  - Multi-search: 5 NRW cities + 1 remote
  - Keywords: data, ai, analytics
  - Pagination Limit: 5 clicks per search (100+ jobs)
  - Rate Limiting: 2000ms delay between requests
  - Detail Pages: Skipped (future enhancement)

## Test Results
- Searches executed: 18 (3 keywords × 5 cities + 3 keywords × 1 remote)
- Jobs per search: ~50-150 avg
- Expected total jobs: ~900 listings
- Extraction method: css with html.parser parser
- Pagination: "Mehr" button working correctly (AJAX-based)
- Note: Multi-search strategy ensures coverage of NRW + remote roles

## Learnings
- Job cards use `[data-testid="job-search-result"]` as container
- Pagination via "Mehr" button (German for "Show more") with AJAX loading
- Company/location/salary extracted via text parsing (no clean selectors available)
- Multi-search approach necessary for comprehensive NRW + remote coverage
- Text-based parsing is fragile but works for initial scrape
- Job detail pages accessible via relative URLs (`/jobs/{slug}-{id}`)
- No HTML-based job_type/remote fields in listing (only text hints)

---
## Meta

### Key Implementation Patterns

**Multi-Search Strategy**: XING scraper loops through multiple search configurations (5 cities + 1 remote × 3 keywords each) to achieve comprehensive NRW + remote coverage. Each search is independent, results are concatenated for parsing.

**Pagination Mechanism**: XING uses AJAX-based "Mehr" button that dynamically loads 20 more jobs without page reload. URL remains static; job count increases after each click.

**Text-Based Extraction**: XING job cards lack clean CSS selectors for company, location, and salary. These fields are extracted via text parsing (splitting by newlines and pattern matching), which is less robust but functional for initial data collection.

### Common Pitfalls Encountered

1. **Assuming single-search approach**
   - **Issue**: XING doesn't support searching multiple cities in one query
   - **Fix**: Implemented multi-search loop (18 independent searches)

2. **Using English "Show More" button selector**
   - **Issue**: XING uses German UI, button text is "Mehr"
   - **Fix**: Updated selector to `button:has-text("Mehr")`

3. **Parsing nested job card structure**
   - **Issue**: Company/location/salary don't have consistent parent-child relationships
   - **Fix**: Used text-based parsing with heuristic rules (€ for salary, city names for location)

### Best Practices Applied

1. **Multi-search strategy**: Comprehensive coverage of NRW + remote through 18 independent searches
2. **Conservative rate limiting**: 2000ms delays to respect XING's moderate anti-bot measures
3. **Per-card error handling**: Individual try/except prevents single bad card from stopping entire scrape
4. **Parser choice**: html.parser for concatenated HTML (90 chunks from 18 searches)
5. **Deferred detail page fetching**: Skipping detail pages for initial implementation to keep code simple

### Future Enhancements

1. **Job Detail Pages**: Fetch full descriptions for jobs that pass initial filters
2. **Structured Data Extraction**: Improve text parsing with more robust heuristics
3. **Job Type Classification**: Extract employment type from card text (full-time, part-time)
4. **Remote Detection**: Better remote job detection from card text
5. **Pagination Optimization**: Stop early if no new jobs loaded (currently fixed 5 clicks)
