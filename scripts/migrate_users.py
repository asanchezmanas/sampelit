import asyncio
import os
import asyncpg
from pathlib import Path

# Add project root to path for imports
import sys
sys.path.append(os.getcwd())

from data_access.database import get_database

async def migrate():
    db = await get_database()
    async with db.pool.acquire() as conn:
        print("Checking users table schema...")
        columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users'
        """)
        column_names = [c['column_name'] for c in columns]
        print(f"Current columns: {column_names}")
        
        if 'role' not in column_names:
            print("Adding 'role' column...")
            await conn.execute("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'client'")
            
        if 'company' not in column_names:
            print("Adding 'company' column...")
            await conn.execute("ALTER TABLE users ADD COLUMN company VARCHAR(255)")
            
        if 'name' not in column_names:
            print("Adding 'name' column...")
            await conn.execute("ALTER TABLE users ADD COLUMN name VARCHAR(255)")
            
        print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
