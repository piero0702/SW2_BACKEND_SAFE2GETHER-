from fastapi import APIRouter, Depends
import logging
from app.services.areas_interes_service import AreasInteresService
from app.models.area_interes import AreaInteresCreate, AreaInteresOut, AreaInteresUpdate

router = APIRouter(prefix="/AreasInteres", tags=["AreasInteres"])

logger = logging.getLogger(__name__)


def get_service() -> AreasInteresService:
    return AreasInteresService()


@router.get("", response_model=list[AreaInteresOut])
async def list_areas(service: AreasInteresService = Depends(get_service)):
    """Lista todas las áreas de interés"""
    return await service.list_areas()


@router.get("/user/{user_id}", response_model=list[AreaInteresOut])
async def list_by_user(user_id: int, service: AreasInteresService = Depends(get_service)):
    """Obtiene todas las áreas de interés de un usuario específico"""
    return await service.list_by_user(user_id)


@router.get("/{area_id}/riesgo")
async def get_nivel_riesgo(
    area_id: int, 
    dias: int = 7,
    service: AreasInteresService = Depends(get_service)
):
    """
    Calcula el nivel de riesgo de un área basado en reportes recientes
    
    - **dias**: Número de días a analizar (por defecto 7)
    - Retorna: nivel de peligro, cantidad de reportes, tipos de delitos
    """
    return await service.calcular_nivel_riesgo(area_id, dias)


@router.post("", response_model=AreaInteresOut, status_code=201)
async def create_area(data: AreaInteresCreate, service: AreasInteresService = Depends(get_service)):
    """Crea una nueva área de interés"""
    logger.debug("Payload a Supabase (AreaInteres): %s", data.model_dump())
    return await service.create_area(data)


@router.patch("/{area_id}", response_model=AreaInteresOut)
async def update_area(area_id: int, data: AreaInteresUpdate, service: AreasInteresService = Depends(get_service)):
    """Actualiza un área de interés existente"""
    return await service.update_area(area_id, data)


@router.delete("/{area_id}")
async def delete_area(area_id: int, service: AreasInteresService = Depends(get_service)):
    """Elimina un área de interés"""
    return await service.delete_area(area_id)


@router.put("/{area_id}", response_model=AreaInteresOut)
async def replace_area(area_id: int, data: AreaInteresCreate, service: AreasInteresService = Depends(get_service)):
    """Reemplaza completamente un área de interés"""
    return await service.update_area(area_id, data)


@router.get("/{area_id}", response_model=AreaInteresOut)
async def get_area(area_id: int, service: AreasInteresService = Depends(get_service)):
    """Obtiene una área de interés por ID"""
    return await service.get_area(area_id)
