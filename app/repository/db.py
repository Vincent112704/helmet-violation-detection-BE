from supabase import create_client, Client
import os


SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]

supabase: Client = create_client(
    supabase_url=SUPABASE_URL,
    supabase_key=SUPABASE_SECRET_KEY
)
