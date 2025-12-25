import asyncio
import os
import sys

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_access.database import DatabaseManager

async def run_migration():
    print("Initializing Database Manager...")
    db = DatabaseManager()
    await db.initialize()
    
    print("Reading schema_audit.sql...")
    with open('database/schema/schema_audit.sql', 'r') as f:
        sql = f.read()
        
    print("Executing migration...")
    async with db.pool.acquire() as conn:
        await conn.execute(sql)
        
    print("Migration complete!")
    await db.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
