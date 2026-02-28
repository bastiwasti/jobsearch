# JobSearch

Single-user job scraping app. Scrapes job listings from the web via Chrome (Playwright), filters them through global regex rules, and displays them in a web dashboard.

## Architecture

- **Monorepo**: `backend/` (Python) + `frontend/` (Next.js)
- **Backend**: Python 3.12+, FastAPI, Playwright, SQLAlchemy, Alembic
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS, shadcn/ui
- **Database**: PostgreSQL (via Docker)
- **Communication**: Frontend → REST API → PostgreSQL ← Backend

## Data Flow

```
Scrape sites → Extract ALL listings → Global regex filter → Store matching jobs in PostgreSQL
                                                              ↓ (separate command)
                                                  python main.py refine → LLM enriches stored jobs
```

## Backend Structure

```
backend/
├── main.py              # CLI: scrape, refine, list-sites
├── server.py            # FastAPI: uvicorn server:app --reload
├── config.py            # Env-based config from .env
├── rules/
│   ├── base.py          # BaseSite class (fetch + parse in one)
│   ├── models.py        # JobListing dataclass
│   ├── common.py        # Shared utilities (extraction, browser, normalization)
│   ├── filters.py       # Global regex rules: INCLUDE/EXCLUDE/LOCATION patterns
│   ├── registry.py      # Auto-discovery of site files
│   ├── companies/       # Direct company career pages (one .py per site)
│   └── aggregators/     # Job boards like LinkedIn, StepStone (one .py per site)
├── scraper/
│   ├── engine.py        # Shared Playwright browser instance
│   └── pipeline.py      # Orchestrator: scrape → filter → dedup → store
├── db/
│   ├── models.py        # SQLAlchemy ORM (Job, ScrapeRun)
│   ├── connection.py    # Engine + session factory
│   └── migrations/      # Alembic migrations
├── api/
│   ├── app.py           # FastAPI app + CORS
│   ├── schemas.py       # Pydantic models
│   └── routes/          # jobs, runs, sites, health
└── llm/
    └── fallback.py      # LLM refinement (separate from scraping)
```

## Key Patterns

### Site Rules
Each site is a single `.py` file in `rules/companies/` or `rules/aggregators/`:
- Subclass `BaseSite`
- Set `name`, `base_url`, `needs_browser`
- Implement `fetch(page) -> str` and `parse(html) -> list[JobListing]`
- Use helpers from `rules/common.py` (extract_text, dismiss_cookie_banner, etc.)

### Global Filters (`rules/filters.py`)
- `INCLUDE_PATTERNS` — domain + leadership keywords (bilingual DE/EN)
- `EXCLUDE_PATTERNS` — Junior, Trainee, Werkstudent, Praktikum, unpaid
- `REMOTE_PATTERNS` — if matched, job accepted from anywhere in the world
- `LOCAL_PATTERNS` — Rheinland ~50km from Monheim (only for non-remote jobs)

### Auto-Discovery
`rules/registry.py` auto-discovers all `BaseSite` subclasses from `companies/` and `aggregators/` folders. No manual registration needed.

## Commands

```bash
# Development
docker compose up -d                         # Start PostgreSQL
cd backend && alembic upgrade head           # Run migrations
cd backend && uvicorn server:app --reload    # Start API server

# Scraping
cd backend && python main.py scrape                  # Scrape all sites
cd backend && python main.py scrape --site linkedin  # Scrape one site
cd backend && python main.py scrape --dry-run        # Preview without storing
cd backend && python main.py refine                  # LLM-enrich jobs
cd backend && python main.py list-sites              # Show registered scrapers

# Frontend
cd frontend && npm run dev                   # Start dev server
```

## Database

PostgreSQL tables:
- `jobs` — scraped job listings with user-action columns (bookmark, status, notes)
- `scrape_runs` — scrape execution history

Dedup: `UNIQUE(url)` on normalized URLs (tracking params stripped).

## Documentation

```
backend/docs/
├── 00_index.md                    # Documentation index
├── 00_site_setup_guide.md         # Agent guide: how to set up a new scraper autonomously
├── sites/
│   ├── _template.md               # Template for per-site documentation
│   └── {site_name}.md             # Per-site: approach, selectors, learnings
└── autonomous/
    └── {site_name}_{date}.md      # Autonomous run logs
```

### Adding a new site scraper

Follow `docs/00_site_setup_guide.md`. The 5-phase process:
1. **Research** — find the careers page, determine the best URL and approach
2. **Investigate** — inspect HTML, map selectors, test pagination, create `docs/sites/{name}.md`
3. **Implement** — create `rules/{companies|aggregators}/{name}.py`
4. **Test** — dry-run, full run, API verification
5. **Document** — update site docs with results and learnings

## Conventions

- Python: type hints, dataclasses, async for browser operations
- One file per site scraper, use common.py helpers
- Filters are global (in filters.py), not per-scraper
- LLM refinement is always opt-in, never automatic
- Frontend fetches via REST API, never direct DB access
- Every site scraper gets documentation in `docs/sites/{name}.md`
- Autonomous runs get logged in `docs/autonomous/`
