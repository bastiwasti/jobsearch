#!/usr/bin/env python3
"""MCP Server for JobSearch database - read-only access."""

import os
import asyncio
from typing import Any
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jobsearch_readonly:LaqBttd1aw6F5u9m@localhost:5432/jobsearch")

server = Server("jobsearch-db")

async def execute_query(query: str, params: list = None) -> list[dict]:
    """Execute a read-only query and return results."""
    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params or [])
            return await cur.fetchall()


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available database tables as resources."""
    return [
        Resource(
            uri="db:///jobs",
            name="Jobs Table",
            description="All scraped job listings with filtering capabilities",
            mimeType="application/json"
        ),
        Resource(
            uri="db:///scrape_runs",
            name="Scrape Runs Table",
            description="History of scraping operations",
            mimeType="application/json"
        ),
        Resource(
            uri="db:///schema/jobs",
            name="Jobs Schema",
            description="Schema definition for jobs table",
            mimeType="application/json"
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a database resource."""
    if uri == "db:///jobs":
        query = """
            SELECT id, title, company, location, url, posted_date, 
                   source_site, status, is_bookmarked, is_hidden, created_at
            FROM jobs
            ORDER BY created_at DESC
            LIMIT 100
        """
        results = await execute_query(query)
        return str(results)
    
    elif uri == "db:///scrape_runs":
        query = """
            SELECT id, started_at, completed_at, status, 
                   sites_scraped, jobs_found, jobs_matched, jobs_new, trigger
            FROM scrape_runs
            ORDER BY started_at DESC
            LIMIT 50
        """
        results = await execute_query(query)
        return str(results)
    
    elif uri == "db:///schema/jobs":
        schema = {
            "table": "jobs",
            "columns": [
                {"name": "id", "type": "integer", "description": "Primary key"},
                {"name": "run_id", "type": "integer", "description": "Foreign key to scrape_runs"},
                {"name": "title", "type": "text", "description": "Job title"},
                {"name": "company", "type": "text", "description": "Company name"},
                {"name": "location", "type": "text", "description": "Job location"},
                {"name": "url", "type": "text", "description": "Unique job URL"},
                {"name": "description", "type": "text", "description": "Job description"},
                {"name": "salary", "type": "text", "description": "Salary information"},
                {"name": "job_type", "type": "varchar(50)", "description": "full-time, part-time, etc."},
                {"name": "remote", "type": "varchar(50)", "description": "remote, hybrid, on-site"},
                {"name": "posted_date", "type": "timestamp", "description": "When job was posted"},
                {"name": "source_site", "type": "varchar(100)", "description": "Scraper source"},
                {"name": "status", "type": "varchar(50)", "description": "new, interested, applied, etc."},
                {"name": "is_bookmarked", "type": "boolean", "description": "User bookmarked"},
                {"name": "is_hidden", "type": "boolean", "description": "User hidden"},
                {"name": "notes", "type": "text", "description": "User notes"},
                {"name": "created_at", "type": "timestamp", "description": "Record creation time"},
            ]
        }
        return str(schema)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available database query tools."""
    return [
        Tool(
            name="query_jobs",
            description="Query the jobs table with filters. Returns job listings matching criteria.",
            inputSchema={
                "type": "object",
                "properties": {
                    "where": {
                        "type": "string",
                        "description": "SQL WHERE clause (e.g., 'status = \"interested\"' or 'source_site = \"google\"')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50, max: 500)",
                        "default": 50
                    },
                    "order_by": {
                        "type": "string",
                        "description": "ORDER BY clause (e.g., 'created_at DESC' or 'posted_date DESC')",
                        "default": "created_at DESC"
                    }
                }
            }
        ),
        Tool(
            name="get_job_stats",
            description="Get statistics about jobs: count by status, source, company, etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "group_by": {
                        "type": "string",
                        "description": "Field to group by: status, source_site, company, job_type, remote",
                        "enum": ["status", "source_site", "company", "job_type", "remote"]
                    }
                },
                "required": ["group_by"]
            }
        ),
        Tool(
            name="search_jobs",
            description="Full-text search in job titles and descriptions",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search terms to find in title or description"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 50)",
                        "default": 50
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_scrape_runs",
            description="Get history of scraping operations",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent runs to return (default: 10)",
                        "default": 10
                    }
                }
            }
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Any) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Execute a database tool."""
    
    if name == "query_jobs":
        where_clause = arguments.get("where", "1=1")
        limit = min(arguments.get("limit", 50), 500)
        order_by = arguments.get("order_by", "created_at DESC")
        
        query = f"""
            SELECT id, title, company, location, url, posted_date, 
                   source_site, status, is_bookmarked, remote, job_type,
                   created_at
            FROM jobs
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT %s
        """
        results = await execute_query(query, [limit])
        return [TextContent(type="text", text=str(results))]
    
    elif name == "get_job_stats":
        group_by = arguments["group_by"]
        query = f"""
            SELECT {group_by}, COUNT(*) as count
            FROM jobs
            GROUP BY {group_by}
            ORDER BY count DESC
        """
        results = await execute_query(query)
        return [TextContent(type="text", text=str(results))]
    
    elif name == "search_jobs":
        search_query = f"%{arguments['query']}%"
        limit = min(arguments.get("limit", 50), 500)
        
        query = """
            SELECT id, title, company, location, url, posted_date, 
                   source_site, status, is_bookmarked, remote, job_type
            FROM jobs
            WHERE title ILIKE %s OR description ILIKE %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        results = await execute_query(query, [search_query, search_query, limit])
        return [TextContent(type="text", text=str(results))]
    
    elif name == "get_scrape_runs":
        limit = arguments.get("limit", 10)
        query = """
            SELECT id, started_at, completed_at, status, 
                   sites_scraped, jobs_found, jobs_matched, jobs_new, 
                   trigger, errors
            FROM scrape_runs
            ORDER BY started_at DESC
            LIMIT %s
        """
        results = await execute_query(query, [limit])
        return [TextContent(type="text", text=str(results))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jobsearch-db",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
