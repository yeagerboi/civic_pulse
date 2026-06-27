import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DB_URL")

async def main():
    if not DB_URL:
        print("Error: DB_URL environment variable not set.")
        return
        
    db_url = DB_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "sslmode=" in db_url:
        db_url = db_url.replace("sslmode=", "ssl=")
        
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR;"))
            print("Successfully added hashed_password column.")
        except Exception as e:
            print(f"Error (might already exist): {e}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
