#!/usr/bin/env python3
"""Test script for MCP server database connection."""

import asyncio
import os
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jobsearch_readonly:LaqBttd1aw6F5u9m@localhost:5432/jobsearch")

async def test_connection():
    """Test database connection and queries."""
    try:
        print("Connecting to database...")
        async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                
                # Test 1: Count jobs
                print("\n1. Total jobs count:")
                await cur.execute("SELECT COUNT(*) as count FROM jobs")
                result = await cur.fetchone()
                print(f"   {result['count']} jobs in database")
                
                # Test 2: Jobs by source
                print("\n2. Jobs by source:")
                await cur.execute("""
                    SELECT source_site, COUNT(*) as count 
                    FROM jobs 
                    GROUP BY source_site 
                    ORDER BY count DESC
                """)
                for row in await cur.fetchall():
                    print(f"   {row['source_site']}: {row['count']}")
                
                # Test 3: Recent jobs
                print("\n3. Most recent job:")
                await cur.execute("""
                    SELECT title, company, location, source_site, created_at
                    FROM jobs
                    ORDER BY created_at DESC
                    LIMIT 1
                """)
                result = await cur.fetchone()
                print(f"   {result['title']} at {result['company']}")
                print(f"   Location: {result['location']}")
                print(f"   Source: {result['source_site']}")
                
                # Test 4: Search query
                print("\n4. Search for 'AI' in titles:")
                await cur.execute("""
                    SELECT title, company
                    FROM jobs
                    WHERE title ILIKE '%AI%'
                    LIMIT 5
                """)
                for row in await cur.fetchall():
                    print(f"   - {row['title']} at {row['company']}")
                
                print("\n✅ All tests passed!")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
