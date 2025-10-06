from typing import Any, Dict, List
import logging
import httpx
from fastapi import HTTPException
from app.clients.supabase_client import SupabaseClient, table_url

logger = logging.getLogger(__name__)


class UsersRepository:
    def __init__(self, client: SupabaseClient | None = None):
        self.client = client or SupabaseClient()

    async def list_users(self) -> List[Dict[str, Any]]:
        # SELECT * FROM Usuarios
        res = await self.client.get(table_url(), params={"select": "*"})
        res.raise_for_status()
        return res.json()

    async def get_by_username_ci(self, username: str) -> List[Dict[str, Any]]:
        # Búsqueda case-insensitive exacta con ilike (sin comodines = exacta)
        params = {"select": "*", "user": f"ilike.{username}", "limit": 1}
        res = await self.client.get(table_url(), params=params)
        res.raise_for_status()
        return res.json()

    async def get_by_id(self, user_id: int) -> Dict[str, Any] | None:
        # Obtener un usuario por su id (limit 1)
        params = {"select": "*", "id": f"eq.{user_id}", "limit": 1}
        res = await self.client.get(table_url(), params=params)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error("Supabase get_by_id failed: status=%s url=%s params=%s response_body=%s",
                         exc.response.status_code, exc.request.url, params, body)
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        data = res.json()
        return data[0] if isinstance(data, list) and data else None

    async def create_user(self, payload: dict) -> Dict[str, Any]:
        res = await self.client.post(table_url(), json=payload)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # Log detail to help debugging 4xx/5xx responses from PostgREST/Supabase
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error(
                "Supabase create_user failed: status=%s url=%s payload=%s response_body=%s",
                exc.response.status_code,
                exc.request.url,
                payload,
                body,
            )
            # Convert to FastAPI HTTPException so client receives proper status + detail
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        data = res.json()
        # Supabase devuelve lista cuando Prefer=return=representation
        return data[0] if isinstance(data, list) and data else data

    async def update_user(self, user_id: int, payload: dict) -> Dict[str, Any]:
        # PostgREST update by filter using id
        params = {"id": f"eq.{user_id}", "select": "*"}
        res = await self.client.patch(table_url(), params=params, json=payload)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error("Supabase update_user failed: status=%s url=%s payload=%s response_body=%s",
                         exc.response.status_code, exc.request.url, payload, body)
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        data = res.json()
        return data[0] if isinstance(data, list) and data else data

    async def delete_user(self, user_id: int) -> int:
        # Delete returns number of deleted rows when Prefer header not set; with Prefer=return=representation it returns list
        params = {"id": f"eq.{user_id}"}
        res = await self.client.delete(table_url(), params=params)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error("Supabase delete_user failed: status=%s url=%s params=%s response_body=%s",
                         exc.response.status_code, exc.request.url, params, body)
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        # Try parse returned representation or fallback to status
        try:
            data = res.json()
            # If representation returned, number deleted is len(data)
            return len(data) if isinstance(data, list) else 0
        except Exception:
            return 0
