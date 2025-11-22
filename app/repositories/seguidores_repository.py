from typing import Any, Dict, List
import logging
import httpx
from fastapi import HTTPException
from app.clients.supabase_client import SupabaseClient, table_url

logger = logging.getLogger(__name__)


class SeguidoresRepository:
    def __init__(self, client: SupabaseClient | None = None):
        self.client = client or SupabaseClient()

    def _url(self):
        return table_url('Seguidores')

    async def list_seguidores(self) -> List[Dict[str, Any]]:
        res = await self.client.get(self._url(), params={"select": "*"})
        res.raise_for_status()
        return res.json()

    async def list_seguidores_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtiene la lista de usuarios que siguen a user_id"""
        params = {"select": "*", "seguido_id": f"eq.{user_id}"}
        res = await self.client.get(self._url(), params=params)
        res.raise_for_status()
        return res.json()

    async def list_seguidos_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtiene la lista de usuarios que user_id sigue"""
        params = {"select": "*", "seguidor_id": f"eq.{user_id}"}
        res = await self.client.get(self._url(), params=params)
        res.raise_for_status()
        return res.json()

    async def get_by_id(self, seguidor_id: int) -> Dict[str, Any] | None:
        params = {"select": "*", "id": f"eq.{seguidor_id}", "limit": 1}
        res = await self.client.get(self._url(), params=params)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error(
                "Supabase get_by_id failed: status=%s url=%s params=%s response_body=%s",
                exc.response.status_code, exc.request.url, params, body
            )
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        data = res.json()
        return data[0] if isinstance(data, list) and data else None

    async def check_if_exists(self, seguidor_id: int, seguido_id: int) -> Dict[str, Any] | None:
        """Verifica si ya existe una relación de seguimiento entre dos usuarios"""
        params = {
            "select": "*",
            "seguidor_id": f"eq.{seguidor_id}",
            "seguido_id": f"eq.{seguido_id}",
            "limit": 1
        }
        res = await self.client.get(self._url(), params=params)
        res.raise_for_status()
        data = res.json()
        return data[0] if isinstance(data, list) and data else None

    async def create_seguidor(self, payload: dict) -> Dict[str, Any]:
        res = await self.client.post(self._url(), json=payload)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error(
                "Supabase create_seguidor failed: status=%s url=%s payload=%s response_body=%s",
                exc.response.status_code, exc.request.url, payload, body
            )
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        data = res.json()
        return data[0] if isinstance(data, list) and data else data

    async def update_seguidor(self, seguidor_id: int, payload: dict) -> Dict[str, Any]:
        params = {"id": f"eq.{seguidor_id}", "select": "*"}
        res = await self.client.patch(self._url(), params=params, json=payload)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error(
                "Supabase update_seguidor failed: status=%s url=%s payload=%s response_body=%s",
                exc.response.status_code, exc.request.url, payload, body
            )
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        data = res.json()
        return data[0] if isinstance(data, list) and data else data

    async def delete_seguidor(self, seguidor_id: int) -> int:
        params = {"id": f"eq.{seguidor_id}"}
        res = await self.client.delete(self._url(), params=params)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error(
                "Supabase delete_seguidor failed: status=%s url=%s params=%s response_body=%s",
                exc.response.status_code, exc.request.url, params, body
            )
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        try:
            data = res.json()
            return len(data) if isinstance(data, list) else 0
        except Exception:
            return 0

    async def delete_by_users(self, seguidor_id: int, seguido_id: int) -> int:
        """Elimina una relación de seguimiento específica entre dos usuarios"""
        params = {
            "seguidor_id": f"eq.{seguidor_id}",
            "seguido_id": f"eq.{seguido_id}"
        }
        res = await self.client.delete(self._url(), params=params)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error(
                "Supabase delete_by_users failed: status=%s url=%s params=%s response_body=%s",
                exc.response.status_code, exc.request.url, params, body
            )
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        try:
            data = res.json()
            return len(data) if isinstance(data, list) else 0
        except Exception:
            return 0

    async def update_by_users(self, seguidor_id: int, seguido_id: int, payload: dict) -> Dict[str, Any]:
        """Actualiza una relación de seguimiento específica entre dos usuarios"""
        params = {
            "seguidor_id": f"eq.{seguidor_id}",
            "seguido_id": f"eq.{seguido_id}",
            "select": "*"
        }
        res = await self.client.patch(self._url(), params=params, json=payload)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error(
                "Supabase update_by_users failed: status=%s url=%s payload=%s response_body=%s",
                exc.response.status_code, exc.request.url, payload, body
            )
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        data = res.json()
        return data[0] if isinstance(data, list) and data else data
