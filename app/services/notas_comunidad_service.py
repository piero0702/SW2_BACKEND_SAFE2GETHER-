from fastapi import HTTPException, status
from typing import Any
from app.repositories.notas_comunidad_repository import NotasComunidadRepository
from app.models.nota_comunidad import NotaComunidadCreate, NotaComunidadOut, NotaComunidadUpdate


class NotasComunidadService:
    def __init__(self, repo: NotasComunidadRepository | None = None):
        self.repo = repo or NotasComunidadRepository()

    async def list_notas(self) -> list[NotaComunidadOut]:
        rows = await self.repo.list_notas()
        return [NotaComunidadOut(**row) for row in rows]

    async def list_by_reporte(self, reporte_id: int) -> list[NotaComunidadOut]:
        rows = await self.repo.list_by_reporte(reporte_id)
        return [NotaComunidadOut(**row) for row in rows]

    async def list_by_user(self, user_id: int) -> list[NotaComunidadOut]:
        rows = await self.repo.list_by_user(user_id)
        return [NotaComunidadOut(**row) for row in rows]

    async def create_nota(self, payload: NotaComunidadCreate) -> NotaComunidadOut:
        allowed = {"reporte_id", "user_id", "nota"}
        raw = payload.model_dump()
        sanitized = {k: v for k, v in raw.items() if k in allowed}
        # Validación básica
        nota_text = str(sanitized.get("nota") or "").strip()
        if not nota_text:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La nota no puede estar vacía")
        sanitized["nota"] = nota_text
        created = await self.repo.create_nota(sanitized)
        return NotaComunidadOut(**created)

    async def get_nota(self, nota_id: int) -> NotaComunidadOut:
        row = await self.repo.get_by_id(nota_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota not found")
        return NotaComunidadOut(**row)

    async def update_nota(self, nota_id: int, payload: NotaComunidadUpdate | NotaComunidadCreate) -> NotaComunidadOut:
        allowed = {"reporte_id", "user_id", "nota"}
        raw = payload.model_dump()
        sanitized: dict[str, Any] = {k: v for k, v in raw.items() if k in allowed and v is not None}

        if "nota" in sanitized:
            nota_text = str(sanitized["nota"]).strip()
            if not nota_text:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La nota no puede estar vacía")
            sanitized["nota"] = nota_text

        updated = await self.repo.update_nota(nota_id, sanitized)
        if isinstance(updated, list):
            if not updated:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota not found")
            updated = updated[0]

        return NotaComunidadOut(**updated)

    async def delete_nota(self, nota_id: int) -> dict:
        deleted_count = await self.repo.delete_nota(nota_id)
        return {"deleted": deleted_count}
