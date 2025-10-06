from fastapi import APIRouter, Depends
import logging
from app.services.users_service import UsersService
from app.models.user import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

logger = logging.getLogger(__name__)


def get_service() -> UsersService:
    return UsersService()


@router.get("", response_model=list[UserOut])
async def list_users(service: UsersService = Depends(get_service)):
    return await service.list_users()


@router.post("", response_model=UserOut, status_code=201)
async def create_user(data: UserCreate, service: UsersService = Depends(get_service)):
    # Use logger instead of print for better control
    logger.debug("Payload a Supabase: %s", data.dict())
    return await service.create_user(data)


@router.patch("/{id}", response_model=UserOut)
async def update_user(id: int, data: UserUpdate, service: UsersService = Depends(get_service)):
    return await service.update_user(id, data)


@router.delete("/{id}")
async def delete_user(id: int, service: UsersService = Depends(get_service)):
    return await service.delete_user(id)


@router.put("/{id}", response_model=UserOut)
async def replace_user(id: int, data: UserCreate, service: UsersService = Depends(get_service)):
    # Treat PUT as full replace: pass the validated create model to update
    return await service.update_user(id, data)


@router.get("/{id}", response_model=UserOut)
async def get_user(id: int, service: UsersService = Depends(get_service)):
    return await service.get_user(id)