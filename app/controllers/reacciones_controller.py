from fastapi import APIRouter, Depends
import logging
from app.services.reacciones_service import ReaccionesService
from app.models.reaccion import ReaccionCreate, ReaccionOut, ReaccionUpdate

router = APIRouter(prefix="/Reacciones", tags=["Reacciones"])

logger = logging.getLogger(__name__)


def get_service() -> ReaccionesService:
    return ReaccionesService()


@router.get("", response_model=list[ReaccionOut])
async def list_reacciones(service: ReaccionesService = Depends(get_service)):
    return await service.list_reacciones()


@router.get("/reporte/{reporte_id}", response_model=list[ReaccionOut])
async def list_reacciones_by_reporte(reporte_id: int, service: ReaccionesService = Depends(get_service)):
    return await service.list_by_reporte(reporte_id)


@router.get("/user/{user_id}", response_model=list[ReaccionOut])
async def list_reacciones_by_user(user_id: int, service: ReaccionesService = Depends(get_service)):
    return await service.list_by_user(user_id)


@router.post("", response_model=ReaccionOut, status_code=201)
async def create_reaccion(data: ReaccionCreate, service: ReaccionesService = Depends(get_service)):
    logger.debug("Payload a Supabase (Reaccion): %s", data.model_dump())
    return await service.create_reaccion(data)


@router.patch("/{id}", response_model=ReaccionOut)
async def update_reaccion(id: int, data: ReaccionUpdate, service: ReaccionesService = Depends(get_service)):
    return await service.update_reaccion(id, data)


@router.delete("/{id}")
async def delete_reaccion(id: int, service: ReaccionesService = Depends(get_service)):
    return await service.delete_reaccion(id)


@router.put("/{id}", response_model=ReaccionOut)
async def replace_reaccion(id: int, data: ReaccionCreate, service: ReaccionesService = Depends(get_service)):
    return await service.update_reaccion(id, data)


@router.get("/{id}", response_model=ReaccionOut)
async def get_reaccion(id: int, service: ReaccionesService = Depends(get_service)):
    return await service.get_reaccion(id)
