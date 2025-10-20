import os

SUPABASE_URL = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    # For logging clarity only; do not raise.
    print("Note: SUPABASE_PROJECT_URL / SUPABASE_ANON_KEY not set or not needed server-side right now.")
