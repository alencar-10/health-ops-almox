import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def list_products():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT name, sku, integration_status FROM products"))
        rows = result.all()
        print("\n=== PRODUTOS NO CATÁLOGO ===")
        for row in rows:
            print(f"Nome: {row[0]} | SKU: {row[1]} | Status: {row[2]}")
        print("============================\n")

if __name__ == "__main__":
    asyncio.run(list_products())
