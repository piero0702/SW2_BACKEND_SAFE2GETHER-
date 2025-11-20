from typing import Any, Dict, List
import logging
import httpx
from fastapi import HTTPException
from app.clients.supabase_client import SupabaseClient, table_url
from app.config import settings

logger = logging.getLogger(__name__)


class ReportesRepository:
    def __init__(self, client: SupabaseClient | None = None):
        self.client = client or SupabaseClient()

    async def list_reportes(self, *, limit: int | None = None, offset: int | None = None, order: str | None = None) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"select": "*"}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if order:
            params["order"] = order
        res = await self.client.get(table_url('Reportes'), params=params)
        res.raise_for_status()
        return res.json()

    async def list_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        params = {"select": "*", "user_id": f"eq.{user_id}"}
        res = await self.client.get(table_url('Reportes'), params=params)
        res.raise_for_status()
        return res.json()

    async def get_by_id(self, reporte_id: int) -> Dict[str, Any] | None:
        params = {"select": "*", "id": f"eq.{reporte_id}", "limit": 1}
        res = await self.client.get(table_url('Reportes'), params=params)
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

    async def create_reporte(self, payload: dict) -> Dict[str, Any]:
        res = await self.client.post(table_url('Reportes'), json=payload)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error("Supabase create_reporte failed: status=%s url=%s payload=%s response_body=%s",
                         exc.response.status_code, exc.request.url, payload, body)
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        data = res.json()
        return data[0] if isinstance(data, list) and data else data

    async def update_reporte(self, reporte_id: int, payload: dict) -> Dict[str, Any]:
        params = {"id": f"eq.{reporte_id}", "select": "*"}
        res = await self.client.patch(table_url('Reportes'), params=params, json=payload)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error("Supabase update_reporte failed: status=%s url=%s payload=%s response_body=%s",
                         exc.response.status_code, exc.request.url, payload, body)
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        data = res.json()
        return data[0] if isinstance(data, list) and data else data

    async def delete_reporte(self, reporte_id: int) -> int:
        params = {"id": f"eq.{reporte_id}"}
        res = await self.client.delete(table_url('Reportes'), params=params)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            logger.error("Supabase delete_reporte failed: status=%s url=%s params=%s response_body=%s",
                         exc.response.status_code, exc.request.url, params, body)
            detail = body if isinstance(body, (dict, list, str)) else str(body)
            raise HTTPException(status_code=exc.response.status_code, detail=detail)

        try:
            data = res.json()
            return len(data) if isinstance(data, list) else 0
        except Exception:
            return 0

    async def get_district_statistics(self) -> dict:
        """
        Obtiene estadísticas agrupadas por distrito.
        Retorna: {distrito: {total: int, por_categoria: {categoria: count}}}
        """
        # Obtener todos los reportes con distrito y categoría
        params = {"select": "distrito,categoria,estado,veracidad_porcentaje"}
        res = await self.client.get(table_url('Reportes'), params=params)
        res.raise_for_status()
        reportes = res.json()

        # Agrupar por distrito
        stats = {}
        for r in reportes:
            distrito = r.get("distrito")
            categoria = r.get("categoria", "Otro")
            estado = r.get("estado", "Activo")
            veracidad = r.get("veracidad_porcentaje", 0)
            
            # Solo contar reportes activos con veracidad >= 33%
            if estado == "Activo" and veracidad >= 33:
                # Si no hay distrito, usar "Sin distrito"
                if not distrito or distrito.strip() == "":
                    distrito = "Sin distrito"
                
                if distrito not in stats:
                    stats[distrito] = {
                        "total": 0,
                        "por_categoria": {}
                    }
                
                stats[distrito]["total"] += 1
                
                if categoria not in stats[distrito]["por_categoria"]:
                    stats[distrito]["por_categoria"][categoria] = 0
                stats[distrito]["por_categoria"][categoria] += 1

        return stats
