-- GA4 Properties table for storing selected Google Analytics 4 properties per user
create table if not exists ga4_properties (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) not null,
  property_id text not null,
  display_name text not null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Create unique constraint: one property per user
create unique index if not exists ga4_properties_user_unique on ga4_properties (user_id);

-- Index for property lookups
create index if not exists ga4_properties_property_id_idx on ga4_properties (property_id);

-- Enable Row-Level Security
alter table ga4_properties enable row level security;
