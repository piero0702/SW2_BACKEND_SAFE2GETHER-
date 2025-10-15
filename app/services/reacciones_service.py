from fastapi import HTTPException, status
from typing import Any
from app.repositories.reacciones_repository import ReaccionesRepository
from app.models.reaccion import ReaccionCreate, ReaccionOut, ReaccionUpdate


class ReaccionesService:
    def __init__(self, repo: ReaccionesRepository | None = None):
        self.repo = repo or ReaccionesRepository()

    async def list_reacciones(self) -> list[ReaccionOut]:
        rows = await self.repo.list_reacciones()
        return [ReaccionOut(**row) for row in rows]

    async def list_by_reporte(self, reporte_id: int) -> list[ReaccionOut]:
        rows = await self.repo.list_by_reporte(reporte_id)
        return [ReaccionOut(**row) for row in rows]

    async def list_by_user(self, user_id: int) -> list[ReaccionOut]:
        rows = await self.repo.list_by_user(user_id)
        return [ReaccionOut(**row) for row in rows]

    async def create_reaccion(self, payload: ReaccionCreate) -> ReaccionOut:
        allowed = {"reporte_id", "user_id", "tipo"}
        raw = payload.model_dump()
        sanitized = {k: v for k, v in raw.items() if k in allowed}
        created = await self.repo.create_reaccion(sanitized)
        return ReaccionOut(**created)

    async def get_reaccion(self, reaccion_id: int) -> ReaccionOut:
        row = await self.repo.get_by_id(reaccion_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reaccion not found")
        return ReaccionOut(**row)

    async def update_reaccion(self, reaccion_id: int, payload: ReaccionUpdate | ReaccionCreate) -> ReaccionOut:
        allowed = {"reporte_id", "user_id", "tipo"}
        raw = payload.model_dump()
        sanitized: dict[str, Any] = {k: v for k, v in raw.items() if k in allowed and v is not None}

        updated = await self.repo.update_reaccion(reaccion_id, sanitized)
        if isinstance(updated, list):
            if not updated:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reaccion not found")
            updated = updated[0]

        return ReaccionOut(**updated)

    async def delete_reaccion(self, reaccion_id: int) -> dict:
        deleted_count = await self.repo.delete_reaccion(reaccion_id)
        return {"deleted": deleted_count}
