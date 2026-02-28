# MCP (Model Context Protocol) Integration

## Status

✅ **Working** — MCP server is operational and providing database access tools.

## Overview

This project integrates with Model Context Protocol (MCP) to expose database functionality as tools for AI assistants. The MCP server provides read-only access to the jobs database through a standardized protocol.

## Available MCP Tools

### `jobsearch-db_query_jobs`
Query the jobs table with filters.

**Parameters:**
- `where` (string, optional) — SQL WHERE clause (e.g., `status = "interested"` or `source_site = "google"`)
- `limit` (integer, optional) — Maximum results (default: 50, max: 500)
- `order_by` (string, optional) — ORDER BY clause (default: `created_at DESC`)

**Returns:** Job listings matching criteria.

### `jobsearch-db_get_job_stats`
Get statistics about jobs: count by status, source, company, etc.

**Parameters:**
- `group_by` (required) — Field to group by: `status`, `source_site`, `company`, `job_type`, `remote`

**Returns:** Aggregated job statistics grouped by the specified field.

### `jobsearch-db_search_jobs`
Full-text search in job titles and descriptions.

**Parameters:**
- `query` (required) — Search terms to find in title or description
- `limit` (integer, optional) — Maximum results (default: 50)

**Returns:** Job listings matching the search query.

### `jobsearch-db_get_scrape_runs`
Get history of scraping operations.

**Parameters:**
- `limit` (integer, optional) — Number of recent runs to return (default: 10)

**Returns:** Recent scrape execution logs with metadata.

## Architecture

```
MCP Server (Python) → PostgreSQL Database
       ↓
  MCP Protocol → AI Assistant (via tools)
```

The MCP server runs as a separate process and exposes these database tools through the MCP protocol. AI assistants can call these tools to query, search, and analyze job data without direct database access.

## Usage Example

```
User: Show me all interested jobs from LinkedIn

Assistant calls: jobsearch-db_query_jobs(where='status = "interested" AND source_site = "linkedin"')

User: What are my job statistics by status?

Assistant calls: jobsearch-db_get_job_stats(group_by='status')
```

## Security

- **Read-only access** — All tools are read-only, no write operations
- **No authentication exposure** — Database credentials stay server-side
- **Rate limiting** — Built-in limits on query results (max 500)
- **SQL injection protection** — Parameters are sanitized through MCP layer

## Configuration

MCP server configuration is handled through environment variables (`.env`):
- Database connection settings
- MCP server host/port
- Tool registration

## Development

To verify MCP connectivity:

```bash
# Check if MCP tools are available
# (Depends on your MCP client setup)

# Test database connection
cd backend && python -c "from db.connection import engine; print(engine)"
```
