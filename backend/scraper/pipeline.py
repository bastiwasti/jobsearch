"""Scrape pipeline orchestrator.

Flow: scrape sites → extract all listings → apply EXCLUDE filters → dedup → store.

Note: We save all jobs that pass EXCLUDE rules. INCLUDE patterns have been removed
to collect broader data for later analysis and refinement.
"""

import asyncio
from datetime import datetime, timezone

from rich.console import Console
from rich.table import Table
from sqlalchemy import select

from db.connection import get_session
from db.models import Job, ScrapeRun
from rules.common import normalize_url
from rules.filters import matches_filters
from rules.models import JobListing
from rules.registry import get_site, get_all_sites
from scraper.engine import BrowserEngine

console = Console()


async def run_scrape(
    site_names: list[str] | None = None,
    search_config: dict | None = None,
    dry_run: bool = False,
) -> ScrapeRun | None:
    """Run the scrape pipeline.

    Args:
        site_names: Specific sites to scrape (None = all registered).
        search_config: Search terms/filters passed to site constructors.
        dry_run: If True, scrape and filter but don't store to DB.

    Returns:
        ScrapeRun record (or None if dry_run).
    """
    # Get sites
    if site_names:
        sites = [get_site(name, search_config) for name in site_names]
    else:
        sites = get_all_sites(search_config)

    if not sites:
        console.print("[yellow]No sites registered. Add site files to rules/companies/ or rules/aggregators/.[/yellow]")
        return None

    console.print(f"[bold]Scraping {len(sites)} site(s)...[/bold]")
    
    # Create run record
    session = get_session() if not dry_run else None
    run = None
    if session:
        run = ScrapeRun(status="running")
        session.add(run)
        session.commit()
    
    total_found = 0
    total_excluded = 0
    total_new = 0
    errors = []

    async with BrowserEngine() as engine:
        for site in sites:
            console.print(f"\n[cyan]→ {site.name}[/cyan] ({site.search_url})")

            try:
                # Fetch and parse
                page = await engine.new_page()
                listings, method = await site.fetch_and_parse(page)
                await page.close()

                console.print(f"  Parsed: {len(listings)} listings (method: {method})")
                total_found += len(listings)

                # Apply EXCLUDE filters (no INCLUDE filters)
                # Jobs matching EXCLUDE are rejected, all others pass
                to_store = [
                    listing for listing in listings
                    if matches_filters(listing.title, listing.description, listing.location, listing.company)
                ]
                excluded = len(listings) - len(to_store)
                total_excluded += excluded
                console.print(f"  Passed EXCLUDE filters: {len(to_store)}/{len(listings)} (excluded: {excluded})")

                if dry_run:
                    _print_listings(to_store)
                    continue

                # Dedup and insert
                new_count = _insert_listings(session, to_store, run.id if run else None, method)
                total_new += new_count
                console.print(f"  New jobs stored: {new_count}")

            except Exception as e:
                console.print(f"  [red]Error: {e}[/red]")
                errors.append({"site": site.name, "error": str(e)})

    # Finalize run
    if run and session:
        run.completed_at = datetime.now(timezone.utc)
        run.status = "completed" if not errors else "completed"
        run.sites_scraped = len(sites)
        run.jobs_found = total_found
        run.jobs_excluded = total_excluded
        run.jobs_new = total_new
        run.errors = errors if errors else None
        session.commit()
        session.close()

    # Summary
    console.print(f"\n[bold green]Done.[/bold green] Found: {total_found} | Excluded: {total_excluded} | New: {total_new}")
    if errors:
        console.print(f"[yellow]Errors: {len(errors)} site(s) had issues.[/yellow]")

    return run


def _insert_listings(session, listings: list[JobListing], run_id: int | None, method: str) -> int:
    """Insert listings into DB, skipping duplicates by URL. Returns count of new rows."""
    new_count = 0
    for listing in listings:
        normalized = normalize_url(listing.url)
        existing = session.execute(
            select(Job.id).where(Job.url == normalized)
        ).scalar_one_or_none()

        if existing:
            continue

        posted = None
        if listing.posted_date:
            try:
                posted = datetime.fromisoformat(listing.posted_date)
            except ValueError:
                pass

        job = Job(
            run_id=run_id,
            title=listing.title,
            company=listing.company,
            location=listing.location,
            url=normalized,
            description=listing.description,
            salary=listing.salary,
            job_type=listing.job_type,
            remote=listing.remote,
            posted_date=posted,
            source_site=listing.source_site,
            extraction_method=method,
            raw_data=listing.raw_data,
        )
        session.add(job)
        new_count += 1

    if new_count:
        session.commit()
    return new_count


def _print_listings(listings: list[JobListing]) -> None:
    """Print listings table for dry-run mode."""
    if not listings:
        return
    table = Table(title="Matched Listings (dry run)")
    table.add_column("Title", style="cyan", max_width=40)
    table.add_column("Company", style="green", max_width=25)
    table.add_column("Location", max_width=20)
    table.add_column("Source")
    for listing in listings:
        table.add_row(listing.title, listing.company, listing.location, listing.source_site)
    console.print(table)
