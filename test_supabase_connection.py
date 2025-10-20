import os
import sqlalchemy

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return

    try:
        engine = sqlalchemy.create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT 1"))
            print("✅ Connected successfully!", result.scalar())
    except Exception as e:
        print("❌ Connection failed:", e)

if __name__ == "__main__":
    main()
