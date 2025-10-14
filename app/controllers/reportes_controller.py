# //sw2_backend_safe2gether/app/controllers/reportes_controller.py
from fastapi import APIRouter, Depends
import logging
from app.services.reportes_service import ReportesService
from app.models.reporte import ReporteCreate, ReporteOut, ReporteUpdate

router = APIRouter(prefix="/Reportes", tags=["Reportes"])

logger = logging.getLogger(__name__)


def get_service() -> ReportesService:
    return ReportesService()


@router.get("", response_model=list[ReporteOut])
async def list_reportes(service: ReportesService = Depends(get_service)):
    return await service.list_reportes()


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


@router.get("/{id}", response_model=ReporteOut)
async def get_reporte(id: int, service: ReportesService = Depends(get_service)):
    return await service.get_reporte(id)