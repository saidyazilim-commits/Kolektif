from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(settings.DATABASE_URL)
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
async def get_db():
    async with async_session_maker() as session:
        yield session