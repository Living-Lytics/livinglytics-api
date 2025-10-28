import os
from sqlalchemy import create_engine, text

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL not set")

# Replace postgresql:// with postgresql+psycopg:// for psycopg3
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

# Create engine
engine = create_engine(database_url)

# Run migrations
with engine.connect() as conn:
    # Add password_hash column
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN password_hash TEXT NULL"))
        conn.commit()
        print("✅ Added password_hash column")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("ℹ️  password_hash column already exists")
        else:
            print(f"❌ Error adding password_hash: {e}")
    
    # Add google_sub column
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN google_sub TEXT NULL"))
        conn.commit()
        print("✅ Added google_sub column")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("ℹ️  google_sub column already exists")
        else:
            print(f"❌ Error adding google_sub: {e}")
    
    # Add unique constraint to google_sub
    try:
        conn.execute(text("ALTER TABLE users ADD CONSTRAINT users_google_sub_key UNIQUE (google_sub)"))
        conn.commit()
        print("✅ Added unique constraint on google_sub")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("ℹ️  unique constraint on google_sub already exists")
        else:
            print(f"❌ Error adding unique constraint: {e}")

print("\n✅ Migration complete!")
