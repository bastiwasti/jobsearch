# JobSearch Backend Documentation

## Guides

- [00_site_setup_guide.md](00_site_setup_guide.md) — **Agent setup guide**: How to autonomously implement a new site scraper from just a company name. Read this first.
- [mcp_integration.md](mcp_integration.md) — MCP (Model Context Protocol) integration status and available database tools.

## Active Scrapers

- [Apple](sites/apple.md) — ✅ Working
- [Google](sites/google.md) — ✅ Working

## Disabled Scrapers

- [Amazon](sites/amazon.md) — ❌ Skipped (requires Google OAuth login)

## Site Learnings

Per-site documentation in `sites/`:
- Each site gets a `.md` file documenting the approach, findings, and learnings
- Naming: `sites/{site_name}.md` (e.g. `sites/stepstone.md`)
- Created during the investigation phase, updated after implementation

## Autonomous Run Logs

Timestamped execution logs in `autonomous/`:
- Naming: `autonomous/{site_name}_{YYYY-MM-DD}.md`
- Records: task, approach, files created, test results, issues, final status
