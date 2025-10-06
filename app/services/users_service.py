from fastapi import HTTPException, status
from typing import Any
from app.repositories.users_repository import UsersRepository
from app.models.user import UserCreate, UserOut, UserUpdate


class UsersService:
    def __init__(self, repo: UsersRepository | None = None):
        self.repo = repo or UsersRepository()

    async def list_users(self) -> list[UserOut]:
        rows = await self.repo.list_users()
        return [UserOut(**row) for row in rows]

    async def create_user(self, payload: UserCreate) -> UserOut:
        # 1) Validación de duplicado (case-insensitive)
        existing = await self.repo.get_by_username_ci(payload.user)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El usuario '{payload.user}' ya existe."
            )

        # 2) Crear - sanitizar payload para enviar solo columnas válidas a Supabase
        allowed = {"user", "email", "psswd"}
        raw = payload.model_dump()  # pydantic v2
        sanitized = {k: v for k, v in raw.items() if k in allowed}
        created = await self.repo.create_user(sanitized)
        return UserOut(**created)

    async def get_user(self, user_id: int) -> UserOut:
        row = await self.repo.get_by_id(user_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserOut(**row)

    async def update_user(self, user_id: int, payload: UserUpdate | UserCreate) -> UserOut:
        # sanitize incoming model (UserUpdate may have None fields)
        allowed = {"user", "email", "psswd"}
        raw = payload.model_dump()
        sanitized: dict[str, Any] = {k: v for k, v in raw.items() if k in allowed and v is not None}

        updated = await self.repo.update_user(user_id, sanitized)
        # repo may return a list when Prefer=return=representation is used
        if isinstance(updated, list):
            if not updated:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            updated = updated[0]

        return UserOut(**updated)

    async def delete_user(self, user_id: int) -> dict:
        deleted_count = await self.repo.delete_user(user_id)
        return {"deleted": deleted_count}
