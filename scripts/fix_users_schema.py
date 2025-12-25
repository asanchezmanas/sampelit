import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from data_access.database import get_database

async def fix_schema():
    db = await get_database()
    async with db.pool.acquire() as conn:
        print("Checking columns in 'users' table...")
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
            print("Added 'role' column.")
        
        if 'company' not in column_names:
            print("Adding 'company' column...")
            await conn.execute("ALTER TABLE users ADD COLUMN company VARCHAR(255)")
            print("Added 'company' column.")
            
        if 'name' not in column_names:
            print("Adding 'name' column...")
            await conn.execute("ALTER TABLE users ADD COLUMN name VARCHAR(255)")
            print("Added 'name' column.")

if __name__ == "__main__":
    asyncio.run(fix_schema())
