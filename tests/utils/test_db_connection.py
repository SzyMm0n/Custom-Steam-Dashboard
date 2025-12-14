#!/usr/bin/env python3
"""Test database connection to Neon"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_connection():
    import asyncpg

    # Read from .env
    host = os.getenv("PGHOST")
    port = int(os.getenv("PGPORT", 5432))
    user = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")
    database = os.getenv("PGDATABASE")

    print(f"Attempting connection to Neon:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  User: {user}")
    print(f"  Database: {database}")
    print()

    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            ssl='require'
        )
        print("✅ Connection successful!")

        # Test query
        version = await conn.fetchval('SELECT version()')
        print(f"✅ PostgreSQL version: {version[:50]}...")

        # Test schema creation
        test_schema = "test_connection_check"
        await conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{test_schema}"')
        print(f"✅ Created test schema: {test_schema}")

        # Cleanup
        await conn.execute(f'DROP SCHEMA IF EXISTS "{test_schema}" CASCADE')
        print(f"✅ Cleaned up test schema")

        await conn.close()
        print("\n✅ All checks passed! Database is ready for integration tests.")

    except Exception as e:
        print(f"\n❌ Connection failed: {type(e).__name__}")
        print(f"   {e}")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)

