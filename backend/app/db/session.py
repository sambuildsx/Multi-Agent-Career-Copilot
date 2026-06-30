import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

logger = logging.getLogger("uvicorn")

database_url = settings.DATABASE_URL
# If the DB URL is postgresql, let's make sure it's valid or try to fall back if needed.
if database_url.startswith("postgresql"):
    # We can use it directly. We'll verify connectivity during queries.
    pass
else:
    # default fallback URL
    database_url = "sqlite+aiosqlite:///careeros.db"

try:
    engine = create_async_engine(
        database_url,
        echo=True,
        future=True,
    )
except Exception as e:
    logger.warning(f"Error initializing database engine for {database_url}: {e}. Falling back to SQLite.")
    database_url = "sqlite+aiosqlite:///careeros.db"
    engine = create_async_engine(
        database_url,
        echo=True,
        future=True,
    )

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
