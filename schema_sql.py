import os
from sqlalchemy import text, create_engine

DDL = """
create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  org_id uuid,
  created_at timestamptz default now()
);
create table if not exists data_sources (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id),
  source_name text not null,
  account_ref text,
  access_token text,
  refresh_token text,
  expires_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create table if not exists metrics (
  id bigserial primary key,
  user_id uuid references users(id),
  source_name text not null,
  metric_date date not null,
  metric_name text not null,
  metric_value numeric not null,
  meta jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);
create index if not exists metrics_user_source_date_idx on metrics (user_id, source_name, metric_date);
create index if not exists data_sources_user_source_idx on data_sources (user_id, source_name);
"""

def main():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL not set"); return
    
    # Ensure we're using psycopg (not psycopg2) driver
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    
    eng = create_engine(url, pool_pre_ping=True)
    with eng.begin() as conn:
        conn.execute(text(DDL))
    print("Schema ensured ✅")

if __name__ == "__main__":
    main()
