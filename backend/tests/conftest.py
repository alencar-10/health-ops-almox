import pytest
import asyncio
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.base import Base
from app.core.config import settings
from app.main import app
from httpx import AsyncClient, ASGITransport

# Test DB URL
TEST_DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

@pytest_asyncio.fixture(scope="function")
async def db():
    # Transactional rollback pattern
    async with engine.connect() as conn:
        await conn.begin()
        async with TestingSessionLocal(bind=conn) as session:
            yield session
            await conn.rollback()

@pytest_asyncio.fixture
async def client(db):
    from app.db.session import get_db
    
    async def _get_test_db():
        yield db

    app.dependency_overrides[get_db] = _get_test_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
