"""CLI entry point for JobSearch backend.

Usage:
    python main.py scrape                  # Scrape all active sites
    python main.py scrape --site linkedin  # Scrape one site
    python main.py scrape --dry-run        # Preview without storing
    python main.py refine                  # LLM-enrich unrefined jobs
    python main.py refine --limit 50       # Refine up to 50 jobs
    python main.py list-sites              # Show registered scrapers
"""

import argparse
import asyncio
import sys


def main():
    parser = argparse.ArgumentParser(description="JobSearch scraper CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scrape
    scrape_parser = subparsers.add_parser("scrape", help="Run scrape pipeline")
    scrape_parser.add_argument("--site", type=str, help="Scrape a specific site by name")
    scrape_parser.add_argument("--dry-run", action="store_true", help="Scrape and filter but don't store")

    # refine
    refine_parser = subparsers.add_parser("refine", help="LLM-enrich stored jobs")
    refine_parser.add_argument("--limit", type=int, default=50, help="Max jobs to refine")
    refine_parser.add_argument("--job-id", type=int, help="Refine a specific job by ID")

    # list-sites
    subparsers.add_parser("list-sites", help="Show registered scrapers")

    args = parser.parse_args()

    if args.command == "scrape":
        from scraper.pipeline import run_scrape
        site_names = [args.site] if args.site else None
        asyncio.run(run_scrape(site_names=site_names, dry_run=args.dry_run))

    elif args.command == "refine":
        from llm.fallback import refine_jobs
        job_ids = [args.job_id] if args.job_id else None
        asyncio.run(refine_jobs(job_ids=job_ids, limit=args.limit))

    elif args.command == "list-sites":
        from rules.registry import get_registry
        from rich.console import Console
        from rich.table import Table

        console = Console()
        registry = get_registry()

        if not registry:
            console.print("[yellow]No sites registered.[/yellow]")
            sys.exit(0)

        table = Table(title="Registered Sites")
        table.add_column("Name", style="cyan")
        table.add_column("URL", style="blue")
        table.add_column("Browser", style="green")
        table.add_column("Category")

        for name, cls in sorted(registry.items()):
            module = cls.__module__
            category = "aggregator" if ".aggregators." in module else "company"
            table.add_row(name, cls.base_url, "yes" if cls.needs_browser else "no", category)

        console.print(table)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
