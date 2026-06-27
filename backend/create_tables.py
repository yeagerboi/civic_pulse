import asyncio
import os
import sys

sys.path.append(os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.db.base import Base
import app.models  # Import all models to register them

DB_URL = "postgresql+asyncpg://neondb_owner:npg_5WXwTnHjVM0I@ep-dark-sunset-at77ag4c.c-9.us-east-1.aws.neon.tech/neondb?ssl=require"

async def main():
    print("Connecting to Neon DB...")
    engine = create_async_engine(DB_URL, echo=True)
    
    async with engine.begin() as conn:
        print("Creating extensions...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    print("All tables created successfully!")

if __name__ == "__main__":
    asyncio.run(main())
