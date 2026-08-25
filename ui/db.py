import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Read from env, but default to sync because we might just use sync psycopg2 for simplicity
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:vasan5707@localhost:5432/meeting_agent_new")
if "+asyncpg" in db_url:
    db_url = db_url.replace("+asyncpg", "") # fallback to psycopg2 for basic sync usage

engine = create_engine(db_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
