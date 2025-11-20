# //sw2_backend_safe2gether/app/controllers/reportes_controller.py
from fastapi import APIRouter, Depends, Query
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


@router.get("/{id}", response_model=ReporteOut)
async def get_reporte(id: int, service: ReportesService = Depends(get_service)):
    return await service.get_reporte(id)