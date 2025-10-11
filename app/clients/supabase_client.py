import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)


def supabase_headers() -> dict:
    # PostgREST/Supabase acepta ambos: 'apikey' y 'Authorization: Bearer'
    return {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",  # devuelve el registro creado
    }


def table_url(table_name: str | None = None) -> str:
    """Return the PostgREST table URL for the given table name.

    If table_name is None, falls back to settings.SUPABASE_TABLE to preserve
    backward compatibility with existing callers.
    """
    # Normaliza la base URL para evitar dobles o faltantes '/'
    base = str(settings.SUPABASE_URL).rstrip('/')
    table = table_name or settings.SUPABASE_TABLE
    return f"{base}/rest/v1/{table}"


class SupabaseClient:
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=10)

    async def get(self, url: str, params: dict | None = None):
        logger.debug("GET %s params=%s", url, params)
        return await self._client.get(url, headers=supabase_headers(), params=params)

    async def post(self, url: str, json: dict):
        logger.debug("POST %s json=%s", url, json)
        return await self._client.post(url, headers=supabase_headers(), json=json)

    async def patch(self, url: str, json: dict | None = None, params: dict | None = None):
        logger.debug("PATCH %s params=%s json=%s", url, params, json)
        return await self._client.patch(url, headers=supabase_headers(), params=params, json=json)

    async def delete(self, url: str, params: dict | None = None):
        logger.debug("DELETE %s params=%s", url, params)
        return await self._client.delete(url, headers=supabase_headers(), params=params)

    async def aclose(self):
        await self._client.aclose()