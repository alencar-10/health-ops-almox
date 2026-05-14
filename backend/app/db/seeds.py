import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import TestingSessionLocal # We'll use a sessionmaker
from app.models.manufacturer import Manufacturer
from app.models.active_ingredient import ActiveIngredient
from app.models.product import Product
from sqlalchemy import select

async def seed_master_data(db: AsyncSession):
    """
    Populates the database with standardized master data for consistent testing and operation.
    """
    # 1. Manufacturers
    manufacturers = [
        {"corporate_name": "Medley Farmacêutica", "trade_name": "Medley", "document": "12345678000190"},
        {"corporate_name": "EMS S/A", "trade_name": "EMS", "document": "00348003000110"},
        {"corporate_name": "Eurofarma Laboratórios", "trade_name": "Eurofarma", "document": "61190096000192"},
    ]
    
    for m_data in manufacturers:
        q = select(Manufacturer).where(Manufacturer.document == m_data["document"])
        exists = (await db.execute(q)).scalar_one_or_none()
        if not exists:
            db.add(Manufacturer(**m_data))
            print(f"Seeding manufacturer: {m_data['trade_name']}")

    # 2. Active Ingredients
    ingredients = [
        "Dipirona Monoidratada",
        "Paracetamol",
        "Amoxicilina",
        "Ibuprofeno",
        "Losartana Potássica",
    ]
    
    for name in ingredients:
        q = select(ActiveIngredient).where(ActiveIngredient.name == name)
        exists = (await db.execute(q)).scalar_one_or_none()
        if not exists:
            db.add(ActiveIngredient(name=name))
            print(f"Seeding ingredient: {name}")

    await db.commit()

if __name__ == "__main__":
    # This is just a helper, normally run via a command
    pass
