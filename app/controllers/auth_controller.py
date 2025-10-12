from fastapi import APIRouter, Depends, Header, HTTPException
from app.services.users_service import UsersService
from app.models.user import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_service() -> UsersService:
    return UsersService()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, service: UsersService = Depends(get_service)):
    """Endpoint de login: recibe user + psswd y devuelve token simple.

    Reemplazar la implementación de token por JWT en producción.
    """
    result = await service.authenticate(data.user, data.psswd)
    return result
