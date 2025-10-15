#//sw2_backend_safe2gether/app/controllers/users_controller.py
from fastapi import APIRouter, Depends, Query
import logging
from app.services.users_service import UsersService
from app.models.user import UserCreate, UserOut, UserUpdate
from app.models.user import (
    UserCreate, 
    UserOut, 
    UserUpdate,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetResponse
)

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


# Bulk fetch users by ids: /users/bulk?ids=1,2,3
@router.get("/bulk")
async def bulk_users(ids: str = Query(""), service: UsersService = Depends(get_service)):
    try:
        id_list = [int(x) for x in ids.split(",") if x.strip().isdigit()]
        return await service.get_users_by_ids(id_list)
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"ids inválidos: {e}")

@router.get("/{id}", response_model=UserOut)
async def get_user(id: int, service: UsersService = Depends(get_service)):
    return await service.get_user(id)

@router.post("/password/request-reset", response_model=PasswordResetResponse)
async def request_password_reset(
    data: PasswordResetRequest,
    service: UsersService = Depends(get_service)
):
    """
    Solicita un reset de contraseña.
    Envía un email con link de recuperación (en desarrollo retorna el token).
    """
    result = await service.request_password_reset(data.email)
    return result


@router.get("/password/validate-token/{token}")
async def validate_reset_token(
    token: str,
    service: UsersService = Depends(get_service)
):
    """Valida si un token de reset es válido"""
    try:
        result = await service.validate_reset_token(token)
        return result
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/password/reset")
async def reset_password(
    data: PasswordResetConfirm,
    service: UsersService = Depends(get_service)
):
    """Resetea la contraseña usando el token"""
    try:
        result = await service.reset_password_with_token(
            token=data.token,
            new_password=data.new_password
        )
        return result
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))