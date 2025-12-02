#!/usr/bin/env python3
"""Create aegra database if it doesn't exist."""
import asyncio
import asyncpg
import sys


async def create_database():
    """Create aegra database if it doesn't exist."""
    try:
        # Connect to postgres database to check/create aegra database
        conn = await asyncpg.connect(
            "postgresql://stackagent:dev_password@postgres:5432/postgres"
        )
        
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", "aegra"
        )
        
        if not exists:
            print("Creating aegra database...")
            await conn.execute('CREATE DATABASE aegra')
            print("Database 'aegra' created successfully.")
        else:
            print("Database 'aegra' already exists.")
        
        await conn.close()
        return 0
    except Exception as e:
        print(f"Error creating database: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(create_database()))

