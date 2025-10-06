"""clients package exports

Keep a small explicit public surface for easier imports in the rest of the app.
"""

from .supabase_client import SupabaseClient, table_url

__all__ = ["SupabaseClient", "table_url"]

