# //sw2_backend_safe2gether/app/controllers/reportes_controller.py
from fastapi import APIRouter, Depends, Query
from typing import Optional
import logging
from app.services.reportes_service import ReportesService
from app.models.reporte import ReporteCreate, ReporteOut, ReporteUpdate

router = APIRouter(prefix="/Reportes", tags=["Reportes"])

logger = logging.getLogger(__name__)


def get_service() -> ReportesService:
    return ReportesService()


@router.get("", response_model=list[ReporteOut])
async def list_reportes(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    order: str = Query("created_at.desc"),
    service: ReportesService = Depends(get_service),
):
    return await service.list_reportes(limit=limit, offset=offset, order=order)


@router.get("/user/{user_id}", response_model=list[ReporteOut])
async def list_reportes_by_user(user_id: int, service: ReportesService = Depends(get_service)):
    return await service.list_by_user(user_id)


@router.post("", response_model=ReporteOut, status_code=201)
async def create_reporte(data: ReporteCreate, service: ReportesService = Depends(get_service)):
    logger.debug("Payload a Supabase: %s", data.model_dump())
    return await service.create_reporte(data)


@router.patch("/{id}", response_model=ReporteOut)
async def update_reporte(id: int, data: ReporteUpdate, service: ReportesService = Depends(get_service)):
    return await service.update_reporte(id, data)


@router.delete("/{id}")
async def delete_reporte(id: int, service: ReportesService = Depends(get_service)):
    return await service.delete_reporte(id)


@router.put("/{id}", response_model=ReporteOut)
async def replace_reporte(id: int, data: ReporteCreate, service: ReportesService = Depends(get_service)):
    return await service.update_reporte(id, data)


@router.get("/estadisticas/distritos")
async def get_district_statistics(service: ReportesService = Depends(get_service)):
    """
    Endpoint para obtener estadísticas de seguridad por distrito.
    Retorna la cantidad de reportes agrupados por distrito y tipo de delito.
    """
    return await service.get_district_statistics()

@router.get("/ranking/distritos")
async def get_district_ranking(
    period: str = Query("week", pattern="^(week|month|year)$"),
    categorias: Optional[str] = Query(None, description="Filtrar por tipos de delito (separados por coma)"),
    service: ReportesService = Depends(get_service)
):
    """Ranking de distritos más seguros (menos reportes válidos) para el período indicado.

    period: week | month | year
    categorias: (opcional) filtrar por tipos de delito específicos separados por coma
    """
    # Convertir string separado por comas a lista
    categorias_list = [c.strip() for c in categorias.split(',')] if categorias else None
    return await service.get_district_ranking(period, categorias_list)

@router.post("/{reporte_id}/actualizar-distrito")
async def actualizar_distrito_desde_coordenadas(
    reporte_id: int,
    service: ReportesService = Depends(get_service)
):
    """Actualiza el campo distrito de un reporte basándose en sus coordenadas lat/lon.
    
    Usa Google Maps Reverse Geocoding para obtener el distrito.
    """
    return await service.actualizar_distrito_desde_coordenadas(reporte_id)

@router.post("/actualizar-distritos-masivo")
async def actualizar_distritos_masivo(
    service: ReportesService = Depends(get_service)
):
    """Actualiza el campo distrito de TODOS los reportes que no lo tienen, 
    usando sus coordenadas lat/lon.
    
    Útil para migración inicial de datos.
    """
    return await service.actualizar_distritos_masivo()


@router.get("/{id}", response_model=ReporteOut)
async def get_reporte(id: int, service: ReportesService = Depends(get_service)):
    return await service.get_reporte(id)