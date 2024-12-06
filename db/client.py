from supabase import create_client
from env import supabase_url, supabase_key

if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL and API Key must be set as environment variables.")

print("Connecting to Supabase...")
supabase = create_client(supabase_url, supabase_key)

if not supabase:
    raise ValueError("Failed to connect to Supabase. Check your credentials.")
