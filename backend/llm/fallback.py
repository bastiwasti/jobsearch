"""LLM-based job refinement — separate from the scrape pipeline.

Run via: python main.py refine [--limit 50] [--job-id 123]
Enriches stored jobs with better salary, job_type, remote classification, etc.
"""

from datetime import datetime, timezone

from rich.console import Console
from sqlalchemy import select

from db.connection import get_session
from db.models import Job

console = Console()


async def refine_jobs(
    job_ids: list[int] | None = None,
    limit: int = 50,
    unrefined_only: bool = True,
) -> int:
    """LLM enrichment for stored jobs.

    Args:
        job_ids: Specific job IDs to refine (None = batch mode).
        limit: Max jobs to refine in batch mode.
        unrefined_only: Only refine jobs without refined_at timestamp.

    Returns:
        Number of jobs refined.
    """
    session = get_session()

    # Build query
    query = select(Job)
    if job_ids:
        query = query.where(Job.id.in_(job_ids))
    elif unrefined_only:
        query = query.where(Job.refined_at.is_(None))
    query = query.limit(limit)

    jobs = session.scalars(query).all()

    if not jobs:
        console.print("[yellow]No jobs to refine.[/yellow]")
        return 0

    console.print(f"[bold]Refining {len(jobs)} job(s)...[/bold]")

    refined_count = 0
    for job in jobs:
        try:
            result = _refine_single(job)
            if result:
                job.refined_at = datetime.now(timezone.utc)
                refined_count += 1
                console.print(f"  [green]✓[/green] {job.title} @ {job.company}")
        except Exception as e:
            console.print(f"  [red]✗[/red] {job.title}: {e}")

    session.commit()
    session.close()

    console.print(f"\n[bold green]Refined {refined_count}/{len(jobs)} jobs.[/bold green]")
    return refined_count


def _refine_single(job: Job) -> bool:
    """Refine a single job using LLM. Returns True if updated."""
    try:
        from config import LLM_PROVIDER, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

        if LLM_PROVIDER != "deepseek" or not DEEPSEEK_API_KEY:
            console.print("[yellow]LLM not configured. Set DEEPSEEK_API_KEY in .env[/yellow]")
            return False

        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import JsonOutputParser

        llm = ChatOpenAI(
            model=DEEPSEEK_MODEL,
            api_key=str(DEEPSEEK_API_KEY),
            base_url=DEEPSEEK_BASE_URL,
            temperature=0.0,
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You analyze job listings and extract structured information. "
                "Return valid JSON with these fields (use empty string if unknown):\n"
                "- salary: normalized salary range (e.g. '60000-80000 EUR/year')\n"
                "- job_type: one of 'full-time', 'part-time', 'contract', 'internship', 'freelance'\n"
                "- remote: one of 'remote', 'hybrid', 'on-site'\n"
            )),
            ("human", "Title: {title}\nCompany: {company}\nLocation: {location}\n\nDescription:\n{description}"),
        ])

        chain = prompt | llm | JsonOutputParser()
        result = chain.invoke({
            "title": job.title,
            "company": job.company,
            "location": job.location or "",
            "description": (job.description or "")[:3000],
        })

        # Update fields only if LLM provided a value and current is empty
        if result.get("salary") and not job.salary:
            job.salary = result["salary"]
        if result.get("job_type") and not job.job_type:
            job.job_type = result["job_type"]
        if result.get("remote") and not job.remote:
            job.remote = result["remote"]

        return True

    except ImportError:
        console.print("[yellow]LLM dependencies not installed. Run: pip install -e '.[llm]'[/yellow]")
        return False
