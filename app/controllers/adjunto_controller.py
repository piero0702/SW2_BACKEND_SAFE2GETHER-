# //sw2_backend_safe2gether/app/controllers/reportes_controller.py
from fastapi import APIRouter, Depends, Query, HTTPException
import logging
from app.services.adjunto_service import AdjuntoService
from app.models.adjunto import AdjuntoCreate, AdjuntoOut, AdjuntoUpdate

router = APIRouter(prefix="/Adjunto", tags=["Adjunto"])

logger = logging.getLogger(__name__)


def get_service() -> AdjuntoService:
    return AdjuntoService()


@router.get("", response_model=list[AdjuntoOut])
async def list_adjuntos(service: AdjuntoService = Depends(get_service)):
    return await service.list_adjuntos()


@router.get("/reporte/{reporte_id}", response_model=list[AdjuntoOut])
async def list_adjuntos_by_reporte(reporte_id: int, service: AdjuntoService = Depends(get_service)):
    return await service.list_by_report(reporte_id)


@router.post("", response_model=AdjuntoOut, status_code=201)
async def create_adjunto(data: AdjuntoCreate, service: AdjuntoService = Depends(get_service)):
    logger.debug("Payload a Supabase: %s", data.model_dump())
    return await service.create_adjunto(data)


@router.patch("/{id}", response_model=AdjuntoOut)
async def update_adjunto(id: int, data: AdjuntoUpdate, service: AdjuntoService = Depends(get_service)):
    return await service.update_adjunto(id, data)


@router.delete("/{id}")
async def delete_adjunto(id: int, service: AdjuntoService = Depends(get_service)):
    return await service.delete_adjunto(id)


@router.put("/{id}", response_model=AdjuntoOut)
async def replace_adjunto(id: int, data: AdjuntoCreate, service: AdjuntoService = Depends(get_service)):
    return await service.update_adjunto(id, data)


@router.get("/by-reporte-ids")
async def list_adjuntos_by_reporte_ids(ids: str = Query(""), service: AdjuntoService = Depends(get_service)):
    try:
        id_list = [int(x) for x in ids.split(",") if x.strip().isdigit()]
        return await service.list_by_report_ids(id_list)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"ids inválidos: {e}")

@router.get("/{id}", response_model=AdjuntoOut)
async def get_adjunto(id: int, service: AdjuntoService = Depends(get_service)):
    return await service.get_adjunto(id)