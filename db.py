import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Prioritize direct DATABASE_URL (port 5432) over pooler to avoid pgBouncer prepared statement conflicts
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_CONNECTION_POOLER_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL or SUPABASE_CONNECTION_POOLER_URL not set")

# Ensure we're using psycopg (not psycopg2) driver
if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

# Ensure SSL mode is required (add if not already in URL)
connect_args = {"sslmode": "require"}
if "sslmode=" in DATABASE_URL:
    connect_args = {}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    poolclass=NullPool,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
