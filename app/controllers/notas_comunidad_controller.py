from fastapi import APIRouter, Depends
import logging
from app.services.notas_comunidad_service import NotasComunidadService
from app.models.nota_comunidad import NotaComunidadCreate, NotaComunidadOut, NotaComunidadUpdate

router = APIRouter(prefix="/Notas_Comunidad", tags=["Notas_Comunidad"])

logger = logging.getLogger(__name__)


def get_service() -> NotasComunidadService:
    return NotasComunidadService()


@router.get("", response_model=list[NotaComunidadOut])
async def list_notas(service: NotasComunidadService = Depends(get_service)):
    return await service.list_notas()


@router.get("/reporte/{reporte_id}", response_model=list[NotaComunidadOut])
async def list_notas_by_reporte(reporte_id: int, service: NotasComunidadService = Depends(get_service)):
    return await service.list_by_reporte(reporte_id)


@router.get("/user/{user_id}", response_model=list[NotaComunidadOut])
async def list_notas_by_user(user_id: int, service: NotasComunidadService = Depends(get_service)):
    return await service.list_by_user(user_id)


@router.post("", response_model=NotaComunidadOut, status_code=201)
async def create_nota(data: NotaComunidadCreate, service: NotasComunidadService = Depends(get_service)):
    logger.debug("Payload a Supabase (Nota Comunidad): %s", data.model_dump())
    return await service.create_nota(data)


@router.patch("/{id}", response_model=NotaComunidadOut)
async def update_nota(id: int, data: NotaComunidadUpdate, service: NotasComunidadService = Depends(get_service)):
    return await service.update_nota(id, data)


@router.delete("/{id}")
async def delete_nota(id: int, service: NotasComunidadService = Depends(get_service)):
    return await service.delete_nota(id)


@router.put("/{id}", response_model=NotaComunidadOut)
async def replace_nota(id: int, data: NotaComunidadCreate, service: NotasComunidadService = Depends(get_service)):
    return await service.update_nota(id, data)


@router.get("/{id}", response_model=NotaComunidadOut)
async def get_nota(id: int, service: NotasComunidadService = Depends(get_service)):
    return await service.get_nota(id)
