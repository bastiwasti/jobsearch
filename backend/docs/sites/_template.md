# {Site Name}

## URL

{The URL(s) we scrape}

## Approach

{Pattern: REST API / Static HTML / Dynamic JS / Pagination / Infinite Scroll / Load More}

## Configuration

- **Location Strategy**: {local / global}
- **Pagination Limit**: {max_pages=N}
- **Rate Limiting**: {delay_ms=N}

## Page Structure

{How job listings appear — describe the HTML structure}
{Key CSS selectors for job cards and fields}

## Job Card Fields

| Field | Selector / Path | Notes |
|-------|----------------|-------|
| title | | |
| company | | |
| location | | |
| url | | |
| description | | |
| salary | | |
| job_type | | |
| remote | | |
| posted_date | | |

## Pagination

{How pagination works, or "single page"}
{VERIFIED: page 1 and page 2 have different content? YES/NO}

## Challenges

{Cookie banners, anti-bot, rate limits, login walls, dynamic loading}

## Sample Data

{3+ example job listings from the page, manually extracted}

---

## Implementation

- File: `rules/{category}/{site_name}.py`
- Class: `{ClassName}`
- Pattern: {approach}
- Date: {YYYY-MM-DD}

## Test Results

- Jobs parsed: {N}
- Jobs matched filters: {N}
- Jobs stored (new): {N}

## Learnings

{What worked, what was tricky, gotchas}
