from fastapi import HTTPException, status
from typing import Any
from app.repositories.adjunto_repository import AdjuntosRepository
from app.models.adjunto import AdjuntoCreate, AdjuntoOut, AdjuntoUpdate


class AdjuntoService:
    def __init__(self, repo: AdjuntosRepository | None = None):
        self.repo = repo or AdjuntosRepository()

    async def list_adjuntos(self) -> list[AdjuntoOut]:
        rows = await self.repo.list_adjuntos()
        return [AdjuntoOut(**row) for row in rows]

    async def list_by_report(self, reporte_id: int) -> list[AdjuntoOut]:
        rows = await self.repo.list_by_report(reporte_id)
        return [AdjuntoOut(**row) for row in rows]

    async def create_adjunto(self, payload: AdjuntoCreate) -> AdjuntoOut:
        # sanitize payload
        allowed = {"reporte_id", "tipo", "url"}
        raw = payload.model_dump()
        sanitized = {k: v for k, v in raw.items() if k in allowed}
        created = await self.repo.create_adjunto(sanitized)
        return AdjuntoOut(**created)

    async def get_adjunto(self, adjunto_id: int) -> AdjuntoOut:
        row = await self.repo.get_by_id(adjunto_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adjunto not found")
        return AdjuntoOut(**row)

    async def update_adjunto(self, adjunto_id: int, payload: AdjuntoUpdate | AdjuntoCreate) -> AdjuntoOut:
        allowed = {"reporte_id", "tipo", "url"}
        raw = payload.model_dump()
        sanitized: dict[str, Any] = {k: v for k, v in raw.items() if k in allowed and v is not None}

        updated = await self.repo.update_adjunto(adjunto_id, sanitized)
        if isinstance(updated, list):
            if not updated:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adjunto not found")
            updated = updated[0]

        return AdjuntoOut(**updated)

    async def delete_adjunto(self, adjunto_id: int) -> dict:
        deleted_count = await self.repo.delete_adjunto(adjunto_id)
        return {"deleted": deleted_count}

    async def list_by_report_ids(self, reporte_ids: list[int]) -> list[AdjuntoOut]:
        rows = await self.repo.list_by_reporte_ids(reporte_ids)
        return [AdjuntoOut(**row) for row in rows]
