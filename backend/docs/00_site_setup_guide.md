# Site Scraper Setup Guide (for AI Agents)

This guide enables autonomous implementation of a new job site scraper.
You receive a company or job board name and produce a working scraper.

## Search Profile (what we're looking for)

**Location**: `rules/filters.py` defines the target profile:
- **Domain**: Data, AI, Analytics — leadership positions
- **Levels**: C-level, VP/Director, Head of, Leiter/Bereichsleiter, Manager, Team Lead
- **Languages**: German + English job postings
- **Location**: Rheinland (~50km from Monheim am Rhein) OR 80-100% remote
- **Exclude**: Junior, Trainee, Werkstudent, Praktikum, unpaid

Filtering is handled by `rules/filters.py` — scrapers should extract ALL jobs from a page and let the global filter decide what to keep.

---

## Scraper Configuration Decisions

Document these decisions in your implementation section for each site:

- **Location Strategy**:
  - `local` - Pre-filter by location URLs (recommended for global companies like Apple, Google, Microsoft)
  - `global` - Scrape all jobs, let LOCAL_PATTERNS filter (recommended for regional job boards like StepStone)

- **Pagination Limit**: Number of pages to scrape (e.g., `max_pages=3`)
  - Global companies: `max_pages=2-3` (high volume, mostly irrelevant)
  - Regional job boards: `max_pages=5-10` (more relevant results)

- **Rate Limiting**: Delay between requests in ms (e.g., `delay_ms=1000`)
  - Recommended: `1000-2000ms` between requests to avoid anti-bot detection

- **Team/Category Pre-filter**: Use URL params to filter by relevant teams if available
  - Reduces noise and improves efficiency
  - Example: `?team=MLAI` for Machine Learning and AI team at Apple

---

## Phase 1: Research the Site

**Goal**: Find the best URL to scrape and understand the page structure.

### Steps

1. **Find the careers/jobs page**
   - Search for: `{company_name} careers`, `{company_name} jobs`, `{company_name} stellenangebote`
   - For aggregators: find the search URL with relevant filters pre-applied
   - Look for API endpoints (check Network tab patterns like `/api/jobs`, `/wp-json/`, GraphQL)

2. **Determine the best approach** — one of these patterns:

   | Pattern | When to use | Example |
   |---------|------------|---------|
   | **REST API** | Site has a public JSON API | Indeed API, company ATS APIs |
   | **Static HTML** | Job listings rendered server-side, no JS needed | Simple career pages |
   | **Dynamic JS** | Jobs loaded via JavaScript, need Playwright | Most modern sites |
   | **Pagination** | Multiple pages of results | StepStone search results |
   | **Infinite scroll** | Jobs load on scroll | LinkedIn public search |
   | **Load More button** | Click to load more results | Some career pages |

 3. **Build the search URL** ⚠️ **CRITICAL - Test location filtering thoroughly**
     
     - **Apply Location Strategy** decision (see "Scraper Configuration Decisions" above):
       - For `local` strategy: Pre-filter by location (e.g. `?location=Germany` or country-specific sites)
       - For `global` strategy: Use base search URL without location filters
     
     - **Location filter verification** — TEST BEFORE IMPLEMENTING:
       - Check if site supports region-specific URLs (e.g., `de-de`, `en-us`, `fr-fr`)
       - Try different location parameter formats:
         - `?location=Germany`
         - `?country=DE` or `?country=germany-DEU`
         - `?loc=Berlin` or city-based filters
       - **Verify filter works**: Fetch 2 different location URLs and confirm results differ
       - If EN-US location filter doesn't work, try:
         - Region-specific subdomains: `de.jobs.apple.com`, `uk.example.com/careers`
         - Region-specific paths: `/de-de/search`, `/de/jobs`, `/fr/emplois`
         - Country codes with region: `?country=DE`, `?location=germany-DEU`
       - **Don't assume EN-US works** — many sites require region/country-specific URLs
     
     - Pre-filter by category/team if possible (e.g. `?team=MLAI`, `?category=data,analytics`)
     - The more filtering the site does, less our global filter has to reject
     - For remote jobs: some sites allow `?remote=true` or similar

4. **Document findings in `docs/sites/{site_name}.md`** (see Phase 2)
   - Include your configuration decisions (Location Strategy, max_pages, etc.) in the documentation

---

## Phase 2: Investigation (MANDATORY before coding)

**Goal**: Thoroughly inspect the page before writing any scraper code.

Create `docs/sites/{site_name}.md` with these sections:

```markdown
# {Site Name}

## URL
{The URL we will scrape}

## Approach
{Pattern chosen: REST API / Static HTML / Dynamic JS / etc.}

## Configuration
- Location Strategy: {local / global}
- Pagination Limit: {max_pages=N}
- Rate Limiting: {delay_ms=N}

## Page Structure
{How job listings appear on the page — CSS selectors, HTML structure}

## Job Card Fields
{What fields are available: title, company, location, salary, etc.}
{Map each to a CSS selector or JSON path}

## Pagination
{How pagination works. CRITICAL: verify pages have different content}

## Challenges
{Cookie banners, anti-bot, rate limits, login walls, dynamic loading}

## Sample Data
{3+ example job listings extracted manually from the HTML}
```

### Investigation Checklist
 
- [ ] Fetch the page HTML (use Playwright if JS-rendered)
- [ ] **CRITICAL**: Verify location filter works before implementation
  - [ ] Test 2 different location URLs and confirm results differ
  - [ ] Try region-specific URLs (`de-de`, `en-us`, subdomains)
  - [ ] Test country codes (`?country=DE`, `?location=germany-DEU`)
- [ ] Identify the CSS selectors for job cards
- [ ] Map fields: title, company, location, URL, salary, job_type, remote, posted_date
- [ ] Check for cookie/consent banners that block content
- [ ] Test pagination: **fetch page 1 and page 2, verify content differs**
- [ ] Check for API endpoints (inspect network requests)
- [ ] Extract 3+ sample jobs manually to validate selectors
- [ ] Note any anti-bot measures (captcha, rate limiting, login required)
- [ ] Decide on **Location Strategy** (local pre-filter vs global scrape)
- [ ] Set **pagination limit** based on result volume (2-3 pages for global companies, 5-10 for regional)

## Common Pitfalls

### ⚠️ Location Filter URL Format

**Mistake**: Assuming EN-US with `?location=Germany` works for all sites
**Reality**: Many sites require region-specific URLs and country codes

**Example: Apple**
- ❌ `https://jobs.apple.com/en-us/search?location=Germany` → 5 jobs, empty locations
- ✅ `https://jobs.apple.com/de-de/search?location=germany-DEU` → 25 jobs, German locations

**What to test**:
1. Region-specific subdomains: `de.example.com`, `uk.example.com`
2. Region-specific paths: `/de/jobs`, `/fr/emplois`
3. Country codes: `?country=DE`, `?location=germany-DEU`
4. Always verify: Fetch 2 different URLs and confirm results differ

### ⚠️ Parser Selection for Multi-Page Scrapes

**Mistake**: Using html.parser with concatenated HTML from multiple pages
**Reality**: Multiple DOCTYPE/html/body tags break html.parser

**Solution**: Use html5lib parser (more lenient) or fetch pages separately

**Example**:
```python
# ❌ html.parser fails on:
"<!DOCTYPE><html>...</html><!DOCTYPE><html>...</html>"

# ✅ html5lib handles:
from bs4 import BeautifulSoup as BS
soup = BS(concatenated_html, "html5lib")
```

### ⚠️ Error Handling Per-Card

**Mistake**: Single try/except for entire parse - one bad card stops everything
**Reality**: UI elements, duplicate entries, or malformed HTML can cause individual cards to fail

**Solution**: Wrap each card processing in individual try/except

```python
for i, card in enumerate(job_cards):
    try:
        # process card
    except Exception as e:
        print(f"Skipping card {i+1}: {e}")
        continue
```

### Pagination Safety Check (Critical)

Many sites return IDENTICAL content on page 2 as page 1. Before implementing pagination:

```
1. Fetch page 1, count job listings
2. Fetch page 2, count job listings
3. Compare: are the listings different?
   - YES → implement pagination
   - NO  → single page only, do NOT paginate
```

---

## Phase 3: Implementation

**Goal**: Create the scraper file.

### File location

- Job boards/aggregators: `rules/aggregators/{site_name}.py`
- Company career pages: `rules/companies/{site_name}.py`

### Template

```python
"""Scraper for {Site Name} job listings.

URL: {url}
Pattern: {approach}
Docs: docs/sites/{site_name}.md
"""

from rules.base import BaseSite
from rules.models import JobListing
from rules.common import extract_text, extract_attr, parse_salary, classify_job_type, classify_remote, parse_posted_date


class {ClassName}(BaseSite):
    name = "{site_name}"
    base_url = "{url}"
    needs_browser = True  # Set False for REST API / static HTML

    @property
    def search_url(self) -> str:
        # Build URL with search params (location, category filters)
        return self.base_url

    async def fetch(self, page) -> str:
        await page.goto(self.search_url, wait_until="networkidle")
        await self.dismiss_cookie_banner(page)
        # Add pagination / scroll / load-more as needed
        return await page.content()

    def parse(self, html: str) -> list[JobListing]:
        soup = self.make_soup(html)
        listings = []
        for card in soup.select("{job_card_selector}"):
            listings.append(JobListing(
                title=extract_text(card, "{title_selector}"),
                company=extract_text(card, "{company_selector}"),
                location=extract_text(card, "{location_selector}"),
                url=extract_attr(card, "{link_selector}", "href"),
                description=extract_text(card, "{desc_selector}"),
                salary=parse_salary(extract_text(card, "{salary_selector}")),
                job_type=classify_job_type(extract_text(card, "{type_selector}")),
                remote=classify_remote(extract_text(card, "{remote_selector}")),
                posted_date=parse_posted_date(extract_text(card, "{date_selector}")),
                source_site=self.name,
            ))
        return listings
```

### Class naming

- File: `rules/aggregators/stepstone.py`
- Class: `StepStone(BaseSite)` — CamelCase of the site name
- `name` attribute: `"stepstone"` — lowercase, used as CLI identifier

### Required fields

Every `JobListing` must have at minimum:
- `title` (required)
- `company` (required)
- `url` (required — full URL to the job posting)
- `source_site` (required — always `self.name`)

Optional but valuable:
- `location`, `description`, `salary`, `job_type`, `remote`, `posted_date`

### URL handling

- Always return **absolute URLs** (not relative `/jobs/123`)
- Use `urljoin(self.base_url, relative_path)` if needed
- The pipeline deduplicates by normalized URL (tracking params stripped)

### Common helpers available (from `rules/common.py`)

```python
# HTML extraction
extract_text(element, selector, default="")     # Safe CSS text extraction
extract_attr(element, selector, attr, default="") # Safe attribute extraction
extract_all_text(element, selector)              # All matching elements
make_soup(html, clean=True)                      # Parse HTML

# Browser interaction
await dismiss_cookie_banner(page)                # Click cookie accept
await scroll_to_load(page, max_scrolls=5)        # Infinite scroll
await click_load_more(page, selector, max=5)     # Load More button
await wait_for_content(page, selector)           # Wait for element

# Job normalization
parse_salary(raw)                                # Normalize salary
classify_job_type(raw)                           # full-time/part-time/...
classify_remote(raw)                             # remote/hybrid/on-site
parse_posted_date(raw)                           # "3 days ago" → ISO date
clean_description(html)                          # Strip HTML tags
normalize_url(url)                               # Strip tracking params
```

---

## Phase 4: Testing

### Test 1: Import check

```bash
cd backend && source .venv/bin/activate
python3 -c "from rules.registry import get_registry; print(get_registry())"
```

Verify your new site appears in the registry.

### Test 2: Dry run

```bash
python main.py scrape --site {site_name} --dry-run
```

This scrapes and filters but does NOT store to DB. Check:
- [ ] No import errors
- [ ] Listings are extracted (count > 0)
- [ ] Filter matches look reasonable
- [ ] No crash / timeout

### Test 3: Full run

```bash
python main.py scrape --site {site_name}
```

Check:
- [ ] Jobs appear in database
- [ ] Fields are populated correctly
- [ ] URLs are absolute and valid
- [ ] No duplicates on re-run

### Test 4: API verification

```bash
uvicorn server:app --port 8000 &
curl -s http://localhost:8000/api/jobs | python3 -m json.tool | head -30
```

---

## Phase 5: Document Results

Update `docs/sites/{site_name}.md` with:

```markdown
## Implementation

- File: `rules/{category}/{site_name}.py`
- Class: `{ClassName}`
- Pattern: {approach used}
- Date: {YYYY-MM-DD}

## Test Results

- Jobs parsed: {N}
- Jobs matched filters: {N}
- Jobs stored (new): {N}
- Extraction method: css

## Learnings

{What worked well, what was tricky, gotchas for future reference}
```

Create autonomous run log at `docs/autonomous/{site_name}_{YYYY-MM-DD}.md`:

```markdown
# {Site Name} — Autonomous Setup Log

**Date**: {YYYY-MM-DD}
**Status**: success / partial / failed

## Task
Set up scraper for {site_name}

## Approach
{Pattern chosen and why}

## Files Created/Modified
- `rules/{category}/{site_name}.py`
- `docs/sites/{site_name}.md`

## Test Results
{Output from dry-run and full run}

## Issues & Fixes
{Any problems encountered and how they were resolved}
{Max 3 self-correction attempts before escalating to user}

## Final Status
{Working / needs user input / failed with reason}
```

---

## Self-Correction Rules

- **Maximum 3 attempts** to fix an issue before asking the user
- For each attempt: diagnose → fix → retest → document
- Common issues:
  - Cookie banner blocking content → add `dismiss_cookie_banner()` call
  - Dynamic content not loaded → increase `wait_until` timeout or add explicit waits
  - CSS selectors wrong → re-inspect HTML, update selectors
  - Pagination duplicates → verify pages differ, reduce MAX_PAGES
  - Anti-bot / captcha → document and escalate to user
  - Login required → document and escalate to user

---

## Quick Reference

```
# Scrape one site (dry run)
python main.py scrape --site {name} --dry-run

# Scrape one site (store to DB)
python main.py scrape --site {name}

# List all registered sites
python main.py list-sites

# Check jobs in DB via API
curl http://localhost:8000/api/jobs
```
