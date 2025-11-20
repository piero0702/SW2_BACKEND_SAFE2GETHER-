from fastapi import HTTPException, status
from typing import Any
from app.repositories.seguidores_repository import SeguidoresRepository
from app.models.seguidor import SeguidorCreate, SeguidorOut, SeguidorUpdate


class SeguidoresService:
    def __init__(self, repo: SeguidoresRepository | None = None):
        self.repo = repo or SeguidoresRepository()

    async def list_seguidores(self) -> list[SeguidorOut]:
        rows = await self.repo.list_seguidores()
        return [SeguidorOut(**row) for row in rows]

    async def list_seguidores_by_user(self, user_id: int) -> list[SeguidorOut]:
        """Obtiene la lista de usuarios que siguen a user_id"""
        rows = await self.repo.list_seguidores_by_user(user_id)
        return [SeguidorOut(**row) for row in rows]

    async def list_seguidos_by_user(self, user_id: int) -> list[SeguidorOut]:
        """Obtiene la lista de usuarios que user_id sigue"""
        rows = await self.repo.list_seguidos_by_user(user_id)
        return [SeguidorOut(**row) for row in rows]

    async def create_seguidor(self, payload: SeguidorCreate) -> SeguidorOut:
        allowed = {"seguidor_id", "seguido_id"}
        raw = payload.model_dump()
        sanitized = {k: v for k, v in raw.items() if k in allowed}
        
        # Validación: no puede seguirse a sí mismo
        if sanitized.get("seguidor_id") == sanitized.get("seguido_id"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail="Un usuario no puede seguirse a sí mismo"
            )
        
        # Verificar si ya existe la relación
        existing = await self.repo.check_if_exists(
            sanitized["seguidor_id"], 
            sanitized["seguido_id"]
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Esta relación de seguimiento ya existe"
            )
        
        created = await self.repo.create_seguidor(sanitized)
        return SeguidorOut(**created)

    async def get_seguidor(self, seguidor_id: int) -> SeguidorOut:
        row = await self.repo.get_by_id(seguidor_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seguidor not found")
        return SeguidorOut(**row)

    async def update_seguidor(self, seguidor_id: int, payload: SeguidorUpdate | SeguidorCreate) -> SeguidorOut:
        allowed = {"seguidor_id", "seguido_id"}
        raw = payload.model_dump()
        sanitized: dict[str, Any] = {k: v for k, v in raw.items() if k in allowed and v is not None}

        # Validación: no puede seguirse a sí mismo
        if "seguidor_id" in sanitized and "seguido_id" in sanitized:
            if sanitized["seguidor_id"] == sanitized["seguido_id"]:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                    detail="Un usuario no puede seguirse a sí mismo"
                )

        updated = await self.repo.update_seguidor(seguidor_id, sanitized)
        if isinstance(updated, list):
            if not updated:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seguidor not found")
            updated = updated[0]

        return SeguidorOut(**updated)

    async def delete_seguidor(self, seguidor_id: int) -> dict:
        deleted_count = await self.repo.delete_seguidor(seguidor_id)
        return {"deleted": deleted_count}

    async def unfollow(self, seguidor_id: int, seguido_id: int) -> dict:
        """Elimina una relación de seguimiento específica entre dos usuarios"""
        deleted_count = await self.repo.delete_by_users(seguidor_id, seguido_id)
        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="No se encontró la relación de seguimiento"
            )
        return {"deleted": deleted_count}
