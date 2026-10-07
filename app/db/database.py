from supabase import create_client, Client
from app.core.config import settings


def get_supabase_client() -> Client:
    """Initialize and return Supabase client."""
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError(
            "Supabase credentials not configured. "
            "Set SUPABASE_URL and SUPABASE_KEY environment variables."
        )
    return create_client(settings.supabase_url, settings.supabase_key)


# Lazy initialization
_supabase_client: Client | None = None


def init_supabase() -> Client:
    """Initialize Supabase client (call once at app startup)."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client


def get_db() -> Client:
    """Get cached Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        raise RuntimeError("Supabase not initialized. Call init_supabase() at startup.")
    return _supabase_client
