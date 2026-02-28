# MCP Server for JobSearch - Local VM Setup

This MCP server provides read-only access to JobSearch PostgreSQL database for AI assistants running on this VM (opencode, Claude VS Code plugin, etc.).

## Architecture

```
AI Assistant (on VM) --[stdio]--> MCP Server (on VM) --[localhost]--> PostgreSQL (on VM)
```

All components run locally on the same VM.

## Files

```
/home/vscode/projects/JobHunt/JobSearch/
├── mcp_server.py              # MCP server script
├── mcp_config_local.json       # Local MCP configuration
├── mcp-venv/                 # Python virtual environment
│   └── bin/python            # Python with MCP SDK
└── .env                      # Database credentials
```

## MCP Configuration

For AI assistants on this VM, use this configuration:

```json
{
  "mcpServers": {
    "jobsearch-db": {
      "command": "/home/vscode/projects/JobHunt/JobSearch/mcp-venv/bin/python",
      "args": [
        "/home/vscode/projects/JobHunt/JobSearch/mcp_server.py"
      ],
      "env": {
        "DATABASE_URL": "postgresql://jobsearch_readonly:LaqBttd1aw6F5u9m@localhost:5432/jobsearch"
      }
    }
  }
}
```

## Available Tools

| Tool | Description | Example |
|------|-------------|----------|
| `query_jobs` | Query jobs with filters | `where: "status = 'interested'"` |
| `get_job_stats` | Statistics by field | `group_by: "source_site"` |
| `search_jobs` | Full-text search | `query: "AI OR machine learning"` |
| `get_scrape_runs` | Scraping history | `limit: 10` |

## Available Resources

| Resource | Description |
|----------|-------------|
| `db:///jobs` | 100 most recent jobs |
| `db:///scrape_runs` | 50 most recent scrape runs |
| `db:///schema/jobs` | Jobs table schema |

## Security

✅ Read-only database user (`jobsearch_readonly`)  
✅ No write operations allowed  
✅ All queries parameterized  
✅ Local communication only (localhost)

## Testing

Test database connection:
```bash
/home/vscode/projects/JobHunt/JobSearch/mcp-venv/bin/python test_mcp_db.py
```

Test MCP server:
```bash
/home/vscode/projects/JobHunt/JobSearch/mcp-venv/bin/python mcp_server.py
```

## Credentials

- **Database**: `jobsearch`
- **User**: `jobsearch_readonly`
- **Password**: `LaqBttd1aw6F5u9m`
- **Host**: `localhost`
- **Port**: `5432`

(Stored in `.env` file)
