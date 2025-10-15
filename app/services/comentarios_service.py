from fastapi import HTTPException, status
from typing import Any
from app.repositories.comentarios_repository import ComentariosRepository
from app.models.comentario import ComentarioCreate, ComentarioOut, ComentarioUpdate


class ComentariosService:
    def __init__(self, repo: ComentariosRepository | None = None):
        self.repo = repo or ComentariosRepository()

    async def list_comentarios(self) -> list[ComentarioOut]:
        rows = await self.repo.list_comentarios()
        return [ComentarioOut(**row) for row in rows]

    async def list_by_reporte(self, reporte_id: int) -> list[ComentarioOut]:
        rows = await self.repo.list_by_reporte(reporte_id)
        return [ComentarioOut(**row) for row in rows]

    async def list_by_user(self, user_id: int) -> list[ComentarioOut]:
        rows = await self.repo.list_by_user(user_id)
        return [ComentarioOut(**row) for row in rows]

    async def create_comentario(self, payload: ComentarioCreate) -> ComentarioOut:
        allowed = {"reporte_id", "user_id", "mensaje"}
        raw = payload.model_dump()
        sanitized = {k: v for k, v in raw.items() if k in allowed}
        # Pequeña validación
        msg = str(sanitized.get("mensaje") or "").strip()
        if not msg:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El mensaje no puede estar vacío")
        sanitized["mensaje"] = msg
        created = await self.repo.create_comentario(sanitized)
        return ComentarioOut(**created)

    async def get_comentario(self, comentario_id: int) -> ComentarioOut:
        row = await self.repo.get_by_id(comentario_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentario not found")
        return ComentarioOut(**row)

    async def update_comentario(self, comentario_id: int, payload: ComentarioUpdate | ComentarioCreate) -> ComentarioOut:
        allowed = {"reporte_id", "user_id", "mensaje"}
        raw = payload.model_dump()
        sanitized: dict[str, Any] = {k: v for k, v in raw.items() if k in allowed and v is not None}

        if "mensaje" in sanitized:
            msg = str(sanitized["mensaje"]).strip()
            if not msg:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El mensaje no puede estar vacío")
            sanitized["mensaje"] = msg

        updated = await self.repo.update_comentario(comentario_id, sanitized)
        if isinstance(updated, list):
            if not updated:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentario not found")
            updated = updated[0]

        return ComentarioOut(**updated)

    async def delete_comentario(self, comentario_id: int) -> dict:
        deleted_count = await self.repo.delete_comentario(comentario_id)
        return {"deleted": deleted_count}
