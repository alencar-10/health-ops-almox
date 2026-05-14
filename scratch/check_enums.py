import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5434/almox_db')
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT n.nspname as schema, t.typname as type FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'integration_step_status_enum'"))
        print(f"SPECIFIC ENUM: {res.fetchall()}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
