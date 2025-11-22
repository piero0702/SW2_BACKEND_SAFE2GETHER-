from fastapi import HTTPException, status
from typing import Any, Dict, List
from datetime import datetime, timedelta
import math
from app.repositories.areas_interes_repository import AreasInteresRepository
from app.repositories.reportes_repository import ReportesRepository
from app.models.area_interes import AreaInteresCreate, AreaInteresOut, AreaInteresUpdate


class AreasInteresService:
    def __init__(
        self, 
        repo: AreasInteresRepository | None = None,
        reportes_repo: ReportesRepository | None = None
    ):
        self.repo = repo or AreasInteresRepository()
        self.reportes_repo = reportes_repo or ReportesRepository()

    async def list_areas(self) -> list[AreaInteresOut]:
        rows = await self.repo.list_areas()
        return [AreaInteresOut(**row) for row in rows]

    async def list_by_user(self, user_id: int) -> list[AreaInteresOut]:
        """Obtiene todas las áreas de interés de un usuario"""
        rows = await self.repo.list_by_user(user_id)
        return [AreaInteresOut(**row) for row in rows]

    async def create_area(self, payload: AreaInteresCreate) -> AreaInteresOut:
        allowed = {"user_id", "nombre", "lat", "lon", "radio_metros", "frecuencia_notificacion", "activo"}
        raw = payload.model_dump()
        sanitized = {k: v for k, v in raw.items() if k in allowed}
        
        # Validaciones
        if sanitized.get("frecuencia_notificacion") not in ["diario", "semanal"]:
            sanitized["frecuencia_notificacion"] = "semanal"
        
        if sanitized.get("radio_metros", 0) <= 0:
            sanitized["radio_metros"] = 1000
        
        nombre = str(sanitized.get("nombre", "")).strip()
        if not nombre:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El nombre del área no puede estar vacío"
            )
        
        created = await self.repo.create_area(sanitized)
        return AreaInteresOut(**created)

    async def get_area(self, area_id: int) -> AreaInteresOut:
        row = await self.repo.get_by_id(area_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Área de interés no encontrada"
            )
        return AreaInteresOut(**row)

    async def update_area(self, area_id: int, payload: AreaInteresUpdate | AreaInteresCreate) -> AreaInteresOut:
        allowed = {"nombre", "lat", "lon", "radio_metros", "frecuencia_notificacion", "activo", "ultima_notificacion"}
        raw = payload.model_dump()
        sanitized: dict[str, Any] = {k: v for k, v in raw.items() if k in allowed and v is not None}

        if "frecuencia_notificacion" in sanitized:
            if sanitized["frecuencia_notificacion"] not in ["diario", "semanal"]:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Frecuencia debe ser 'diario' o 'semanal'"
                )

        if "radio_metros" in sanitized and sanitized["radio_metros"] <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El radio debe ser mayor a 0"
            )

        updated = await self.repo.update_area(area_id, sanitized)
        if isinstance(updated, list):
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Área de interés no encontrada"
                )
            updated = updated[0]

        return AreaInteresOut(**updated)

    async def delete_area(self, area_id: int) -> dict:
        deleted_count = await self.repo.delete_area(area_id)
        return {"deleted": deleted_count}

    def _calcular_distancia_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distancia entre dos coordenadas usando fórmula de Haversine"""
        R = 6371  # Radio de la Tierra en km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

    async def calcular_nivel_riesgo(self, area_id: int, dias_analisis: int = 7) -> Dict[str, Any]:
        """
        Analiza reportes recientes en el área y calcula nivel de riesgo
        
        Returns:
            - nivel_peligro: "Bajo", "Medio", "Alto"
            - total_reportes: cantidad de reportes en el área
            - tipos_delitos: dict con cantidad por categoría
            - reportes_recientes: lista de reportes en el área
        """
        area = await self.repo.get_by_id(area_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Área no encontrada"
            )
        
        # Obtener reportes recientes (últimos N días)
        todos_reportes = await self.reportes_repo.list_reportes(limit=1000, order="created_at.desc")
        
        # Filtrar por fecha
        fecha_limite = datetime.now() - timedelta(days=dias_analisis)
        reportes_recientes = []
        
        for reporte in todos_reportes:
            # Verificar fecha
            created_at = reporte.get("created_at")
            if created_at:
                try:
                    fecha_reporte = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if fecha_reporte < fecha_limite:
                        continue
                except Exception:
                    pass
            
            # Calcular distancia
            lat_reporte = reporte.get("lat")
            lon_reporte = reporte.get("lon")
            
            if lat_reporte is not None and lon_reporte is not None:
                distancia_km = self._calcular_distancia_km(
                    area["lat"],
                    area["lon"],
                    lat_reporte,
                    lon_reporte
                )
                
                # Si está dentro del radio, incluirlo
                radio_km = area.get("radio_metros", 1000) / 1000
                if distancia_km <= radio_km:
                    reportes_recientes.append(reporte)
        
        # Calcular estadísticas
        total_reportes = len(reportes_recientes)
        tipos_delitos: Dict[str, int] = {}
        
        for reporte in reportes_recientes:
            categoria = reporte.get("categoria", "Otro")
            tipos_delitos[categoria] = tipos_delitos.get(categoria, 0) + 1
        
        # Determinar nivel de peligro
        if total_reportes == 0:
            nivel_peligro = "Bajo"
        elif total_reportes <= 3:
            nivel_peligro = "Bajo"
        elif total_reportes <= 10:
            nivel_peligro = "Medio"
        else:
            nivel_peligro = "Alto"
        
        return {
            "area_id": area_id,
            "area_nombre": area.get("nombre"),
            "nivel_peligro": nivel_peligro,
            "total_reportes": total_reportes,
            "tipos_delitos": tipos_delitos,
            "dias_analisis": dias_analisis,
            "reportes_recientes": reportes_recientes[:10]  # Solo los primeros 10 para no saturar
        }
