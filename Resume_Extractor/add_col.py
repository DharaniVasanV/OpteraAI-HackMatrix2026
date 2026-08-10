import asyncio
from sqlalchemy import text
from src.resume_extractor.core.database import async_engine

async def add_user_email():
    async with async_engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE resumes ADD COLUMN user_email VARCHAR(255)"))
            print("Successfully added user_email column to resumes table.")
        except Exception as e:
            print("Error or already exists:", e)

if __name__ == "__main__":
    asyncio.run(add_user_email())
