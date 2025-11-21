from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone
import logging
import httpx
from fastapi import HTTPException
from app.clients.supabase_client import SupabaseClient, table_url
from app.config import settings

logger = logging.getLogger(__name__)

# Constants
REPORTES_TABLE = 'Reportes'
MIN_VERACIDAD_PORCENTAJE = 33
ESTADO_ACTIVO = "Activo"
SIN_DISTRITO = "Sin distrito"
SIN_CATEGORIA = "Sin categoría"


class ReportesRepository:
    def __init__(self, client: SupabaseClient | None = None):
        self.client = client or SupabaseClient()

    def _build_query_params(
        self,
        select: str = "*",
        limit: int | None = None,
        offset: int | None = None,
        order: str | None = None,
        **filters
    ) -> Dict[str, Any]:
        """Helper to build query parameters."""
        params: Dict[str, Any] = {"select": select}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if order:
            params["order"] = order
        params.update(filters)
        return params

    def _handle_http_error(self, exc: httpx.HTTPStatusError, operation: str, **context) -> None:
        """Centralized error handling for HTTP errors."""
        try:
            body = exc.response.json()
        except Exception:
            body = exc.response.text
        
        logger.error(
            "Supabase %s failed: status=%s url=%s context=%s response_body=%s",
            operation, exc.response.status_code, exc.request.url, context, body
        )
        detail = body if isinstance(body, (dict, list, str)) else str(body)
        raise HTTPException(status_code=exc.response.status_code, detail=detail)

    def _extract_first_result(self, data: Any) -> Dict[str, Any]:
        """Extract the first result from Supabase response."""
        return data[0] if isinstance(data, list) and data else data

    async def list_reportes(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        order: str | None = None
    ) -> List[Dict[str, Any]]:
        """List all reportes with optional pagination and ordering."""
        params = self._build_query_params(limit=limit, offset=offset, order=order)
        res = await self.client.get(table_url(REPORTES_TABLE), params=params)
        res.raise_for_status()
        return res.json()

    async def list_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """List all reportes for a specific user."""
        params = self._build_query_params(user_id=f"eq.{user_id}")
        res = await self.client.get(table_url(REPORTES_TABLE), params=params)
        res.raise_for_status()
        return res.json()

    async def list_reportes_from_followed_users(self, user_id: int) -> List[Dict[str, Any]]:
        """List reportes from users that user_id follows."""
        # Primero obtenemos la lista de usuarios seguidos
        seguidores_params = {"select": "seguido_id", "seguidor_id": f"eq.{user_id}"}
        seguidores_res = await self.client.get(table_url('Seguidores'), params=seguidores_params)
        seguidores_res.raise_for_status()
        seguidos_data = seguidores_res.json()
        
        if not seguidos_data:
            return []
        
        # Extraer los IDs de los usuarios seguidos
        seguido_ids = [item['seguido_id'] for item in seguidos_data if 'seguido_id' in item]
        
        if not seguido_ids:
            return []
        
        # Obtener reportes de esos usuarios
        # Usar el operador 'in' de PostgREST
        seguido_ids_str = f"({','.join(map(str, seguido_ids))})"
        params = self._build_query_params(
            user_id=f"in.{seguido_ids_str}",
            order="created_at.desc"
        )
        res = await self.client.get(table_url(REPORTES_TABLE), params=params)
        res.raise_for_status()
        return res.json()

    async def get_by_id(self, reporte_id: int) -> Dict[str, Any] | None:
        """Get a single reporte by ID."""
        params = self._build_query_params(id=f"eq.{reporte_id}", limit=1)
        res = await self.client.get(table_url(REPORTES_TABLE), params=params)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, "get_by_id", params=params)

        data = res.json()
        return data[0] if isinstance(data, list) and data else None

    async def create_reporte(self, payload: dict) -> Dict[str, Any]:
        """Create a new reporte."""
        res = await self.client.post(table_url(REPORTES_TABLE), json=payload)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, "create_reporte", payload=payload)

        return self._extract_first_result(res.json())

    async def update_reporte(self, reporte_id: int, payload: dict) -> Dict[str, Any]:
        """Update an existing reporte."""
        params = {"id": f"eq.{reporte_id}", "select": "*"}
        res = await self.client.patch(table_url(REPORTES_TABLE), params=params, json=payload)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, "update_reporte", reporte_id=reporte_id, payload=payload)

        return self._extract_first_result(res.json())

    async def delete_reporte(self, reporte_id: int) -> int:
        """Delete a reporte by ID."""
        params = {"id": f"eq.{reporte_id}"}
        res = await self.client.delete(table_url(REPORTES_TABLE), params=params)
        try:
            res.raise_for_status()
        except httpx.HTTPStatusError as exc:
            self._handle_http_error(exc, "delete_reporte", reporte_id=reporte_id)

        try:
            data = res.json()
            return len(data) if isinstance(data, list) else 0
        except Exception:
            return 0

    def _is_valid_reporte(self, reporte: Dict[str, Any]) -> bool:
        """Check if a reporte is valid (active and meets minimum veracidad)."""
        estado = reporte.get("estado", "")
        veracidad = reporte.get("veracidad_porcentaje", 0)
        return estado == ESTADO_ACTIVO and veracidad >= MIN_VERACIDAD_PORCENTAJE

    def _normalize_distrito(self, distrito: str | None) -> str:
        """Normalize distrito name, returning default if empty."""
        return distrito if distrito and distrito.strip() else SIN_DISTRITO

    async def get_district_statistics(self) -> dict:
        """
        Get statistics grouped by district.
        Returns: {distrito: {total: int, por_categoria: {categoria: count}}}
        """
        params = self._build_query_params(select="distrito,categoria,estado,veracidad_porcentaje")
        res = await self.client.get(table_url(REPORTES_TABLE), params=params)
        res.raise_for_status()
        reportes = res.json()

        stats = {}
        for reporte in reportes:
            if not self._is_valid_reporte(reporte):
                continue
            
            distrito = self._normalize_distrito(reporte.get("distrito"))
            categoria = reporte.get("categoria", "Otro")
            
            if distrito not in stats:
                stats[distrito] = {"total": 0, "por_categoria": {}}
            
            stats[distrito]["total"] += 1
            stats[distrito]["por_categoria"][categoria] = stats[distrito]["por_categoria"].get(categoria, 0) + 1

        return stats

    def _calculate_period_start(self, period: str) -> datetime:
        """Calculate the start date based on the period."""
        period = (period or "week").lower().strip()
        now = datetime.now(timezone.utc)
        
        period_days = {
            "year": 365,
            "month": 30,
            "week": 7
        }
        days = period_days.get(period, 7)
        return now - timedelta(days=days)

    def _parse_created_at(self, created_at_str: str | None) -> datetime | None:
        """Parse created_at string to datetime."""
        if not created_at_str:
            return None
        try:
            return datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    async def get_district_ranking(
        self,
        period: str = "week",
        categorias: Optional[List[str]] = None
    ) -> list[dict]:
        """
        Get district ranking (safer districts have fewer valid reports).

        Args:
            period: "week" | "month" | "year"
            categorias: Optional list of categories to filter

        Returns:
            List ordered by total_delitos (ascending):
            [{distrito, total_delitos, resoluciones_autoridades, porcentaje_resoluciones, 
              periodo, desde, hasta, por_categoria}]
        """
        start = self._calculate_period_start(period)
        now = datetime.now(timezone.utc)

        # Fetch all reportes with necessary fields
        params = self._build_query_params(
            select="distrito,estado,veracidad_porcentaje,created_at,categoria"
        )
        try:
            res = await self.client.get(table_url(REPORTES_TABLE), params=params)
            res.raise_for_status()
            rows = res.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Error in Supabase: {e.response.status_code} - {e.response.text}")
            # Fallback: fetch all columns
            params = self._build_query_params()
            res = await self.client.get(table_url(REPORTES_TABLE), params=params)
            res.raise_for_status()
            rows = res.json()
        
        start_iso = start.strftime("%Y-%m-%dT%H:%M:%S")
        end_iso = now.strftime("%Y-%m-%dT%H:%M:%S")

        agg: Dict[str, Dict[str, Any]] = {}
        
        for reporte in rows:
            # Filter by creation date
            created_at = self._parse_created_at(reporte.get("created_at"))
            if created_at and created_at < start:
                continue
            
            distrito = self._normalize_distrito(reporte.get("distrito"))
            categoria = reporte.get("categoria") or SIN_CATEGORIA

            # Filter by categories if specified
            if categorias and categoria not in categorias:
                continue

            # Initialize district data if not exists
            if distrito not in agg:
                agg[distrito] = {
                    "distrito": distrito,
                    "total_delitos": 0,
                    "resoluciones_autoridades": 0,
                    "por_categoria": {},
                }
            
            # Count valid reportes
            if self._is_valid_reporte(reporte):
                agg[distrito]["total_delitos"] += 1
                agg[distrito]["resoluciones_autoridades"] += 1
                agg[distrito]["por_categoria"][categoria] = agg[distrito]["por_categoria"].get(categoria, 0) + 1

        # Build ranking list
        ranking = [
            {
                "distrito": data["distrito"],
                "total_delitos": data["total_delitos"],
                "resoluciones_autoridades": data["resoluciones_autoridades"],
                "porcentaje_resoluciones": round(
                    (data["resoluciones_autoridades"] / data["total_delitos"] * 100.0)
                    if data["total_delitos"] > 0 else 0.0,
                    2
                ),
                "periodo": period,
                "desde": start_iso,
                "hasta": end_iso,
                "por_categoria": data["por_categoria"],
            }
            for data in agg.values()
        ]

        # Sort by total_delitos (ascending - fewer crimes = safer)
        ranking.sort(key=lambda x: x["total_delitos"])
        return ranking

    def _find_district_in_components(self, address_components: List[Dict[str, Any]]) -> Optional[str]:
        """
        Find district name in address components based on priority.
        Priority order: sublocality_level_1, sublocality_level_2, sublocality, 
                       administrative_area_level_3, locality
        """
        type_priorities = [
            "sublocality_level_1",
            "sublocality_level_2",
            "sublocality",
            "administrative_area_level_3",
            "locality"
        ]
        
        for priority_type in type_priorities:
            for component in address_components:
                types = component.get("types", [])
                if priority_type in types:
                    distrito = component.get("long_name")
                    logger.info(f"✓ District found ({priority_type}): {distrito}")
                    return distrito
        
        return None

    async def get_distrito_from_coordinates(self, lat: float, lon: float) -> Optional[str]:
        """
        Get district name from coordinates using Google Maps Reverse Geocoding API.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            District name or None if not found
        """
        if not settings.GOOGLE_MAPS_API_KEY:
            logger.error("GOOGLE_MAPS_API_KEY is not configured")
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
                    logger.error(
                        f"Google Maps API error: {data.get('status')} - {data.get('error_message', '')}"
                    )
                    return None
                
                results = data.get("results", [])
                if not results:
                    logger.warning(f"No results found for lat={lat}, lon={lon}")
                    return None
                
                logger.info(f"Processing {len(results)} Google Maps results for lat={lat}, lon={lon}")
                
                # Search for district in all results
                for result in results:
                    address_components = result.get("address_components", [])
                    formatted_address = result.get("formatted_address", "")
                    logger.debug(f"Formatted address: {formatted_address}")
                    
                    distrito = self._find_district_in_components(address_components)
                    if distrito:
                        return distrito
                
                # Log available components if nothing found
                if results:
                    logger.warning("No district found. Available components:")
                    for component in results[0].get("address_components", []):
                        logger.warning(
                            f"  - {component.get('long_name')} ({', '.join(component.get('types', []))})"
                        )
                
                return None
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error querying Google Maps API: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_distrito_from_coordinates: {e}", exc_info=True)
            return None
