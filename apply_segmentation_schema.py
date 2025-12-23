import asyncio
import os
import asyncpg
from pathlib import Path

async def apply_schema():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL not set")
        return

    # Supabase URL fix (standard for this project)
    if "supabase.co" in database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    print(f"Connecting to database...")
    conn = await asyncpg.connect(database_url)
    
    schema_path = Path("segmentation/schema_segmentation.sql")
    if not schema_path.exists():
        print(f"Error: Schema file not found at {schema_path}")
        await conn.close()
        return

    print(f"Reading schema from {schema_path}...")
    schema_sql = schema_path.read_text(encoding='utf-8')

    print("Executing schema...")
    try:
        # Split by sections if needed, but asyncpg.execute can handle multiple statements
        await conn.execute(schema_sql)
        print("✅ Schema applied successfully!")
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(apply_schema())
