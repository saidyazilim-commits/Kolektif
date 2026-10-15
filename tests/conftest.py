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


async def register_and_login(client, email, password="pytest-sifresi-1"):
    # Adım 1: kayıt (test_register_success'tekinin aynısı)
    response = await client.post("/users/register", json={"email": email, "password": password})
    assert response.status_code == 200

    # Adım 2: giriş
    response = await client.post("/users/login", json={"email": email, "password": password})

    # Adım 3: cevaptan token'ı çıkar
    token = response.json()["access_token"]

    # Adım 4: header sözlüğünü döndür
    return {"Authorization": f"Bearer {token}"}

async def make_column(client, headers):
    # column_id fixture'ının gövdesi, owner_headers yerine headers kullanarak
    # 1. workspace
    response = await client.post("/workspaces/", json={"name": "task_test_ws"}, headers=headers)
    assert response.status_code == 200
    ws_id = response.json()["id"]

    # 2. board
    response = await client.post(f"/workspaces/{ws_id}/boards", json={"name": "task_test_board"}, headers=headers)
    assert response.status_code == 200
    board_id = response.json()["id"]

    # 3. kolon
    response = await client.post(f"/boards/{board_id}/columns", json={"name": "To Do", "position": 0}, headers=headers)
    assert response.status_code == 200
    return response.json()["id"]

@pytest.fixture
async def owner_headers(client):
    return await register_and_login(client, "owner@example.com")

@pytest.fixture
async def stranger_headers(client):
    return await register_and_login(client, "stranger@example.com")

@pytest.fixture
async def column_id(client, owner_headers):
    return await make_column(client, owner_headers)

@pytest.fixture
async def foreign_column_id(client, stranger_headers):
    return await make_column(client, stranger_headers)

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