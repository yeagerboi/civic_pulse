from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings

db_url = settings.DB_URL
# Railway/Neon injects 'postgresql://', but we need 'postgresql+asyncpg://' for our async driver
if db_url and db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
# asyncpg expects 'ssl=require' instead of 'sslmode=require'
if db_url and "sslmode=" in db_url:
    db_url = db_url.replace("sslmode=", "ssl=")

engine = create_async_engine(db_url, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
