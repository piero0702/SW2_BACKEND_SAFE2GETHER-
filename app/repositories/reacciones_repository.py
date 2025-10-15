from typing import Any, Dict, List
import logging
import httpx
from fastapi import HTTPException
from app.clients.supabase_client import SupabaseClient, table_url

logger = logging.getLogger(__name__)


class ReaccionesRepository:
    def __init__(self, client: SupabaseClient | None = None):
        self.client = client or SupabaseClient()

    def _url(self):
        return table_url('Reaccion')

    async def list_reacciones(self) -> List[Dict[str, Any]]:
        res = await self.client.get(self._url(), params={"select": "*"})
        res.raise_for_status()
        return res.json()

    async def list_by_reporte(self, reporte_id: int) -> List[Dict[str, Any]]:
        params = {"select": "*", "reporte_id": f"eq.{reporte_id}"}
        res = await self.client.get(self._url(), params=params)
        res.raise_for_status()
        return res.json()

    async def list_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        params = {"select": "*", "user_id": f"eq.{user_id}"}
        res = await self.client.get(self._url(), params=params)
        res.raise_for_status()
        return res.json()

    async def get_by_id(self, reaccion_id: int) -> Dict[str, Any] | None:
        params = {"select": "*", "id": f"eq.{reaccion_id}", "limit": 1}
        res = await self.client.get(self._url(), params=params)
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

    async def create_reaccion(self, payload: dict) -> Dict[str, Any]:
        res = await self.client.post(self._url(), json=payload)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error("Supabase create_reaccion failed: status=%s url=%s payload=%s response_body=%s",
                         exc.response.status_code, exc.request.url, payload, body)
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        data = res.json()
        return data[0] if isinstance(data, list) and data else data

    async def update_reaccion(self, reaccion_id: int, payload: dict) -> Dict[str, Any]:
        params = {"id": f"eq.{reaccion_id}", "select": "*"}
        res = await self.client.patch(self._url(), params=params, json=payload)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error("Supabase update_reaccion failed: status=%s url=%s payload=%s response_body=%s",
                         exc.response.status_code, exc.request.url, payload, body)
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        data = res.json()
        return data[0] if isinstance(data, list) and data else data

    async def delete_reaccion(self, reaccion_id: int) -> int:
        params = {"id": f"eq.{reaccion_id}"}
        res = await self.client.delete(self._url(), params=params)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error("Supabase delete_reaccion failed: status=%s url=%s params=%s response_body=%s",
                         exc.response.status_code, exc.request.url, params, body)
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        try:
            data = res.json()
            return len(data) if isinstance(data, list) else 0
        except Exception:
            return 0
