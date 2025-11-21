from fastapi import APIRouter, Depends
import logging
from app.services.seguidores_service import SeguidoresService
from app.models.seguidor import SeguidorCreate, SeguidorOut, SeguidorUpdate

router = APIRouter(prefix="/Seguidores", tags=["Seguidores"])

logger = logging.getLogger(__name__)


def get_service() -> SeguidoresService:
    return SeguidoresService()


@router.get("", response_model=list[SeguidorOut])
async def list_seguidores(service: SeguidoresService = Depends(get_service)):
    return await service.list_seguidores()


@router.get("/seguidores/{user_id}", response_model=list[SeguidorOut])
async def list_seguidores_by_user(user_id: int, service: SeguidoresService = Depends(get_service)):
    """Obtiene la lista de usuarios que siguen a user_id"""
    return await service.list_seguidores_by_user(user_id)


@router.get("/seguidos/{user_id}", response_model=list[SeguidorOut])
async def list_seguidos_by_user(user_id: int, service: SeguidoresService = Depends(get_service)):
    """Obtiene la lista de usuarios que user_id sigue"""
    return await service.list_seguidos_by_user(user_id)


@router.get("/is-following/{seguidor_id}/{seguido_id}")
async def is_following(seguidor_id: int, seguido_id: int, service: SeguidoresService = Depends(get_service)):
    """Verifica si seguidor_id sigue a seguido_id"""
    return await service.is_following(seguidor_id, seguido_id)


@router.post("", response_model=SeguidorOut, status_code=201)
async def create_seguidor(data: SeguidorCreate, service: SeguidoresService = Depends(get_service)):
    logger.debug("Payload a Supabase (Seguidor): %s", data.model_dump())
    return await service.create_seguidor(data)


@router.delete("/unfollow/{seguidor_id}/{seguido_id}")
async def unfollow(seguidor_id: int, seguido_id: int, service: SeguidoresService = Depends(get_service)):
    """Elimina una relación de seguimiento específica entre dos usuarios"""
    return await service.unfollow(seguidor_id, seguido_id)


@router.patch("/{id}", response_model=SeguidorOut)
async def update_seguidor(id: int, data: SeguidorUpdate, service: SeguidoresService = Depends(get_service)):
    return await service.update_seguidor(id, data)


@router.delete("/{id}")
async def delete_seguidor(id: int, service: SeguidoresService = Depends(get_service)):
    return await service.delete_seguidor(id)


@router.put("/{id}", response_model=SeguidorOut)
async def replace_seguidor(id: int, data: SeguidorCreate, service: SeguidoresService = Depends(get_service)):
    return await service.update_seguidor(id, data)


@router.get("/{id}", response_model=SeguidorOut)
async def get_seguidor(id: int, service: SeguidoresService = Depends(get_service)):
    return await service.get_seguidor(id)
