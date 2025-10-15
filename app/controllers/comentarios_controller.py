from fastapi import APIRouter, Depends
import logging
from app.services.comentarios_service import ComentariosService
from app.models.comentario import ComentarioCreate, ComentarioOut, ComentarioUpdate

router = APIRouter(prefix="/Comentarios", tags=["Comentarios"])

logger = logging.getLogger(__name__)


def get_service() -> ComentariosService:
    return ComentariosService()


@router.get("", response_model=list[ComentarioOut])
async def list_comentarios(service: ComentariosService = Depends(get_service)):
    return await service.list_comentarios()


@router.get("/reporte/{reporte_id}", response_model=list[ComentarioOut])
async def list_comentarios_by_reporte(reporte_id: int, service: ComentariosService = Depends(get_service)):
    return await service.list_by_reporte(reporte_id)


@router.get("/user/{user_id}", response_model=list[ComentarioOut])
async def list_comentarios_by_user(user_id: int, service: ComentariosService = Depends(get_service)):
    return await service.list_by_user(user_id)


@router.post("", response_model=ComentarioOut, status_code=201)
async def create_comentario(data: ComentarioCreate, service: ComentariosService = Depends(get_service)):
    logger.debug("Payload a Supabase (Comentario): %s", data.model_dump())
    return await service.create_comentario(data)


@router.patch("/{id}", response_model=ComentarioOut)
async def update_comentario(id: int, data: ComentarioUpdate, service: ComentariosService = Depends(get_service)):
    return await service.update_comentario(id, data)


@router.delete("/{id}")
async def delete_comentario(id: int, service: ComentariosService = Depends(get_service)):
    return await service.delete_comentario(id)


@router.put("/{id}", response_model=ComentarioOut)
async def replace_comentario(id: int, data: ComentarioCreate, service: ComentariosService = Depends(get_service)):
    return await service.update_comentario(id, data)


@router.get("/{id}", response_model=ComentarioOut)
async def get_comentario(id: int, service: ComentariosService = Depends(get_service)):
    return await service.get_comentario(id)
