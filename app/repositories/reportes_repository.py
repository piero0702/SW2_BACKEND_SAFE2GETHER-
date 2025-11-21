from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone
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

    async def get_district_ranking(self, period: str = "week", categorias: Optional[List[str]] = None) -> list[dict]:
        """Devuelve ranking de distritos más seguros (menos reportes válidos) para un período.

        period: "week" | "month" | "year"
        categorias: (opcional) lista de categorías para filtrar
        Regla de "reporte válido": estado == "Activo" y veracidad_porcentaje >= 33.
        Consideramos "resuelto" como veracidad_porcentaje >= 33 (no existe otro campo de resolución).

        Retorna lista ordenada asc por total_delitos:
        [{distrito, total_delitos, resoluciones_autoridades, porcentaje_resoluciones, periodo, desde, hasta, por_categoria}]
        """
        period = (period or "week").lower().strip()
        now = datetime.now(timezone.utc)
        if period == "year":
            start = now - timedelta(days=365)
        elif period == "month":
            start = now - timedelta(days=30)
        else:
            start = now - timedelta(days=7)

        # Obtener todos los reportes con created_at y categoria
        params = {
            "select": "distrito,estado,veracidad_porcentaje,created_at,categoria",
        }
        try:
            res = await self.client.get(table_url('Reportes'), params=params)
            res.raise_for_status()
            rows = res.json()
        except httpx.HTTPStatusError as e:
            # Log del error para debugging
            logger.error(f"Error en Supabase: {e.response.status_code} - {e.response.text}")
            # Si falla, intentar con select=* (todas las columnas)
            params = {"select": "*"}
            res = await self.client.get(table_url('Reportes'), params=params)
            res.raise_for_status()
            rows = res.json()
        
        # Formato de fechas para el resultado
        start_iso = start.strftime("%Y-%m-%dT%H:%M:%S")
        end_iso = now.strftime("%Y-%m-%dT%H:%M:%S")

        agg: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            # Filtrar por fecha created_at
            created_at_str = r.get("created_at")
            if created_at_str:
                try:
                    # Parsear la fecha y comparar
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    if created_at < start:
                        continue  # Saltar reportes fuera del período
                except (ValueError, AttributeError):
                    # Si hay error parseando la fecha, incluir el reporte
                    pass
            
            distrito = r.get("distrito") or "Sin distrito"
            estado = r.get("estado") or ""
            veracidad = r.get("veracidad_porcentaje") or 0
            cat = r.get("categoria") or "Sin categoría"

            # Si hay filtro de categorías, solo contar reportes de esas categorías
            if categorias and cat not in categorias:
                continue

            # Reporte válido para contar delito
            valido = estado == "Activo" and (isinstance(veracidad, (int, float)) and veracidad >= 33)
            if distrito not in agg:
                agg[distrito] = {
                    "distrito": distrito,
                    "total_delitos": 0,
                    "resoluciones_autoridades": 0,
                    "por_categoria": {},
                }
            if valido:
                agg[distrito]["total_delitos"] += 1
                agg[distrito]["resoluciones_autoridades"] += 1  # misma métrica por falta de campo específico
                
                # Agregar conteo por categoría
                if cat not in agg[distrito]["por_categoria"]:
                    agg[distrito]["por_categoria"][cat] = 0
                agg[distrito]["por_categoria"][cat] += 1

        ranking = []
        for distrito, data in agg.items():
            total = data["total_delitos"]
            resueltos = data["resoluciones_autoridades"]
            porcentaje = (resueltos / total * 100.0) if total > 0 else 0.0
            ranking.append({
                "distrito": distrito,
                "total_delitos": total,
                "resoluciones_autoridades": resueltos,
                "porcentaje_resoluciones": round(porcentaje, 2),
                "periodo": period,
                "desde": start_iso,
                "hasta": end_iso,
                "por_categoria": data["por_categoria"],
            })

        # Orden ascendente por total_delitos (menos delitos => más seguro)
        ranking.sort(key=lambda x: x["total_delitos"])
        return ranking

    async def get_distrito_from_coordinates(self, lat: float, lon: float) -> Optional[str]:
        """Obtiene el distrito a partir de coordenadas usando Google Maps Reverse Geocoding API.
        
        Args:
            lat: Latitud
            lon: Longitud
            
        Returns:
            Nombre del distrito o None si no se encuentra
        """
        if not settings.GOOGLE_MAPS_API_KEY:
            logger.error("GOOGLE_MAPS_API_KEY no está configurada")
            return None
        
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "latlng": f"{lat},{lon}",
            "key": settings.GOOGLE_MAPS_API_KEY,
            "language": "es",
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != "OK":
                    logger.error(f"Error en Google Maps API: {data.get('status')} - {data.get('error_message', '')}")
                    return None
                
                results = data.get("results", [])
                if not results:
                    logger.warning(f"No se encontraron resultados para lat={lat}, lon={lon}")
                    return None
                
                logger.info(f"Procesando {len(results)} resultados de Google Maps para lat={lat}, lon={lon}")
                
                # Buscar el componente de distrito en múltiples niveles
                distrito_encontrado = None
                
                for result in results:
                    address_components = result.get("address_components", [])
                    formatted_address = result.get("formatted_address", "")
                    
                    logger.debug(f"Dirección formateada: {formatted_address}")
                    
                    # Prioridad 1: sublocality_level_1 (distrito específico)
                    for component in address_components:
                        types = component.get("types", [])
                        if "sublocality_level_1" in types:
                            distrito_encontrado = component.get("long_name")
                            logger.info(f"✓ Distrito encontrado (sublocality_level_1): {distrito_encontrado}")
                            return distrito_encontrado
                    
                    # Prioridad 2: sublocality_level_2
                    for component in address_components:
                        types = component.get("types", [])
                        if "sublocality_level_2" in types:
                            distrito_encontrado = component.get("long_name")
                            logger.info(f"✓ Distrito encontrado (sublocality_level_2): {distrito_encontrado}")
                            return distrito_encontrado
                    
                    # Prioridad 3: sublocality (distrito general)
                    for component in address_components:
                        types = component.get("types", [])
                        if "sublocality" in types:
                            distrito_encontrado = component.get("long_name")
                            logger.info(f"✓ Distrito encontrado (sublocality): {distrito_encontrado}")
                            return distrito_encontrado
                    
                    # Prioridad 4: administrative_area_level_3 (puede ser distrito en algunos países)
                    for component in address_components:
                        types = component.get("types", [])
                        if "administrative_area_level_3" in types:
                            distrito_encontrado = component.get("long_name")
                            logger.info(f"✓ Distrito encontrado (admin_level_3): {distrito_encontrado}")
                            return distrito_encontrado
                    
                    # Prioridad 5: locality (ciudad/pueblo)
                    for component in address_components:
                        types = component.get("types", [])
                        if "locality" in types:
                            distrito_encontrado = component.get("long_name")
                            logger.info(f"✓ Localidad encontrada: {distrito_encontrado}")
                            return distrito_encontrado
                
                # Si no encontramos nada, loguear todos los componentes para debug
                if not distrito_encontrado and results:
                    logger.warning(f"No se encontró distrito. Componentes disponibles:")
                    for component in results[0].get("address_components", []):
                        logger.warning(f"  - {component.get('long_name')} ({', '.join(component.get('types', []))})")
                
                return None
                
        except httpx.HTTPError as e:
            logger.error(f"Error HTTP al consultar Google Maps API: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en get_distrito_from_coordinates: {e}", exc_info=True)
            return None
