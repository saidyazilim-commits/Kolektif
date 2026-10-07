from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def test_uses_test_database(engine: AsyncEngine):
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT current_database()"))
        db_name = result.scalar()

    assert db_name == "kolektif_test"