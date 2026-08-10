import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def _load_env_file() -> dict:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, ".env")
    if not os.path.exists(env_path):
        return {}
    values = {}
    with open(env_path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            values[key.strip()] = val.strip()
    return values


ENV_VALUES = _load_env_file()
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
default_sqlite_url = f"sqlite:///{os.path.join(project_root, 'meetings.db')}"

RAW_DB_URL = os.getenv("DATABASE_URL") or ENV_VALUES.get("DATABASE_URL") or default_sqlite_url

# Fix legacy 'postgres://' scheme for SQLAlchemy 2.0
if RAW_DB_URL.startswith("postgres://"):
    RAW_DB_URL = RAW_DB_URL.replace("postgres://", "postgresql://", 1)

if "+asyncpg" in RAW_DB_URL:
    RAW_DB_URL = RAW_DB_URL.replace("+asyncpg", "")

# Automatically create database if using PostgreSQL and database does not exist
if RAW_DB_URL.startswith("postgresql"):
    try:
        from sqlalchemy import text
        from sqlalchemy.engine import make_url
        url = make_url(RAW_DB_URL)
        db_name = url.database
        
        # Connect to default 'postgres' database to create the target database
        postgres_url = url._replace(database="postgres")
        temp_engine = create_engine(postgres_url)
        with temp_engine.connect() as conn:
            # Check if database exists
            res = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"))
            if not res.scalar():
                conn.execute(text("commit"))
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Database '{db_name}' created successfully.")
        temp_engine.dispose()
    except Exception as e:
        print(f"Note: Could not automatically verify/create database: {e}")

connect_args = {"check_same_thread": False} if RAW_DB_URL.startswith("sqlite") else {}

try:
    engine = create_engine(RAW_DB_URL, connect_args=connect_args)
    # Test connection
    with engine.connect() as conn:
        pass
except Exception as exc:
    print(f"Warning: Could not connect to primary database '{RAW_DB_URL}': {exc}. Falling back to SQLite.")
    RAW_DB_URL = default_sqlite_url
    engine = create_engine(RAW_DB_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_utc_now():
    return datetime.now(timezone.utc)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)


class Meeting(Base):
    # Renamed from 'meetings' → 'watcher_items' to avoid clash with Meeting Agent
    __tablename__ = "watcher_items"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String, unique=True, index=True, nullable=True)
    user_email = Column(String, index=True, nullable=True)
    organizer = Column(String, nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    platform = Column(String, nullable=True)
    meeting_url = Column(String, nullable=True)
    date = Column(String, nullable=True)  # YYYY-MM-DD
    start_time = Column(String, nullable=True)  # HH:MM
    end_time = Column(String, nullable=True)  # HH:MM
    time_zone = Column(String, nullable=True)
    status = Column(String, default="scheduled")  # scheduled, updated, cancelled
    category = Column(String, default="Meeting")
    email_body = Column(Text, nullable=True)
    priority = Column(String, default="Low")
    priority_score = Column(Integer, default=0)
    priority_explanation = Column(Text, nullable=True)
    priority_thought = Column(Text, nullable=True)
    recommended_actions = Column(Text, nullable=True)
    # Integration cross-reference columns
    email_inbox_id = Column(String, nullable=True)
    classification_id = Column(String, nullable=True)
    priority_id = Column(String, nullable=True)
    research_id = Column(String, nullable=True)
    enrichment_id = Column(Integer, nullable=True)
    calendar_event_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)


def migrate_db():
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    # Create any missing tables defined in Base (watcher_items, categories)
    Base.metadata.create_all(bind=engine)
    
    # Dynamic column migrations on watcher_items
    try:
        table_names = inspector.get_table_names()
        if "watcher_items" not in table_names:
            return  # fresh table created above — no migrations needed
        existing_cols = [c["name"] for c in inspector.get_columns("watcher_items")]
        new_cols = [
            ("category", "VARCHAR DEFAULT 'Meeting'"),
            ("email_body", "TEXT"),
            ("priority", "VARCHAR DEFAULT 'Low'"),
            ("priority_score", "INTEGER DEFAULT 0"),
            ("priority_explanation", "TEXT"),
            ("priority_thought", "TEXT"),
            ("recommended_actions", "TEXT"),
            ("email_inbox_id", "VARCHAR(100)"),
            ("classification_id", "VARCHAR(36)"),
            ("priority_id", "VARCHAR(36)"),
            ("research_id", "VARCHAR(36)"),
            ("enrichment_id", "INTEGER"),
            ("calendar_event_id", "VARCHAR(36)"),
            ("user_email", "VARCHAR(255)"),
        ]
        for col_name, col_def in new_cols:
            if col_name not in existing_cols:
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE watcher_items ADD COLUMN {col_name} {col_def}"))
                    conn.execute(text("commit"))
    except Exception as e:
        print(f"Migration warning: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
