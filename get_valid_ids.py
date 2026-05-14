import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def get_ids():
    async with AsyncSessionLocal() as db:
        tenant = await db.execute(text("SELECT id FROM tenants LIMIT 1"))
        t_id = tenant.scalar()
        
        unit = await db.execute(text("SELECT id FROM units WHERE tenant_id = :tid LIMIT 1"), {"tid": t_id})
        u_id = unit.scalar()
        
        print(f"TENANT_ID={t_id}")
        print(f"UNIT_ID={u_id}")

if __name__ == "__main__":
    asyncio.run(get_ids())
