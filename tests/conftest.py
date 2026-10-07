import pytest

from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app import models # noqa: F401
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import ASGITransport, AsyncClient



@pytest.fixture
async def engine():
    # Make a test engine
    test_engine = create_async_engine(settings.TEST_DATABASE_URL, poolclass=NullPool)
    # check if ends with '_test', if not RuntimeError(...)
    if not test_engine.url.database.endswith("_test"):
        raise RuntimeError(f"Refusing to run tests on database {test_engine.url.database!r}")
    # Make the tables
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield test_engine
    # Clear the tables
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    # Dispose (Stop) the engine
    await test_engine.dispose()

@pytest.fixture
async def client(engine):
    # 1. engine'e bağlı bir session fabrikası (session.py'deki async_session_maker'ın aynısı,
    #    ama bind=engine fixture'ı ve expire_on_commit=False)
    async_session_maker = sessionmaker(bind=engine,class_=AsyncSession, expire_on_commit=False)
    # 2. get_db'nin yerine geçecek async generator (session.py'deki get_db'nin aynısı,
    #    sadece yukarıdaki fabrikayı kullanıyor)
    async def override_get_db():
        async with async_session_maker() as session:
            yield session
    # 3. app.dependency_overrides[get_db] = senin_fonksiyonun
    app.dependency_overrides[get_db] = override_get_db
    # 4. async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
    #        yield ac
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    # 5. temizlik: app.dependency_overrides.clear()
    app.dependency_overrides.clear()