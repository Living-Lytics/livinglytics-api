import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Prioritize direct DATABASE_URL (port 5432) over pooler to avoid pgBouncer prepared statement conflicts
DATABASE_URL = os.getenv("DATABASE_URL")
POOLER_URL = os.getenv("SUPABASE_CONNECTION_POOLER_URL")

if not DATABASE_URL and not POOLER_URL:
    raise RuntimeError("DATABASE_URL or SUPABASE_CONNECTION_POOLER_URL not set")

def convert_to_psycopg(url):
    """Convert database URL to use psycopg driver."""
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    return url

def create_db_engine():
    """Create database engine with IPv4 preference and pooler fallback."""
    # Try direct connection first (preferred for production)
    if DATABASE_URL:
        try:
            url = convert_to_psycopg(DATABASE_URL)
            # Force IPv4 by adding hostaddr parameter to avoid IPv6 connection issues
            connect_args = {
                "sslmode": "require",
                "options": "-c client_encoding=utf8"
            }
            
            engine = create_engine(
                url,
                pool_pre_ping=True,
                poolclass=NullPool,
                connect_args=connect_args,
            )
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logging.info("✅ Using direct database connection (port 5432)")
            return engine
            
        except Exception as e:
            logging.warning(f"⚠️  Direct connection failed (IPv6 issue?): {str(e)[:100]}")
            logging.info("Falling back to connection pooler...")
    
    # Fall back to connection pooler
    if POOLER_URL:
        url = convert_to_psycopg(POOLER_URL)
        connect_args = {"sslmode": "require"}
        
        engine = create_engine(
            url,
            pool_pre_ping=True,
            poolclass=NullPool,
            connect_args=connect_args,
        )
        
        logging.info("✅ Using connection pooler (port 6543)")
        return engine
    
    raise RuntimeError("Could not establish database connection")

engine = create_db_engine()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
