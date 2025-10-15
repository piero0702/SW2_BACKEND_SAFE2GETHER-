from fastapi import HTTPException, status
from typing import Any
from app.repositories.reportes_repository import ReportesRepository
from app.models.reporte import ReporteCreate, ReporteOut, ReporteUpdate


class ReportesService:
    def __init__(self, repo: ReportesRepository | None = None):
        self.repo = repo or ReportesRepository()

    async def list_reportes(self) -> list[ReporteOut]:
        rows = await self.repo.list_reportes()
        return [ReporteOut(**row) for row in rows]

    async def list_by_user(self, user_id: int) -> list[ReporteOut]:
        rows = await self.repo.list_by_user(user_id)
        return [ReporteOut(**row) for row in rows]

    async def create_reporte(self, payload: ReporteCreate) -> ReporteOut:
        # sanitize payload
        allowed = {"user_id", "titulo", "descripcion", "categoria", "lat", "lon", "direccion", "estado", "veracidad_porcentaje", "cantidad_upvotes", "cantidad_downvotes"}
        raw = payload.model_dump()
        sanitized = {k: v for k, v in raw.items() if k in allowed}
        # Force default veracidad when not provided by client
        if sanitized.get("veracidad_porcentaje") is None:
            sanitized["veracidad_porcentaje"] = 0.0
        created = await self.repo.create_reporte(sanitized)
        return ReporteOut(**created)

    async def get_reporte(self, reporte_id: int) -> ReporteOut:
        row = await self.repo.get_by_id(reporte_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporte not found")
        return ReporteOut(**row)

    async def update_reporte(self, reporte_id: int, payload: ReporteUpdate | ReporteCreate) -> ReporteOut:
        allowed = {"titulo", "descripcion", "categoria", "lat", "lon", "direccion", "estado", "veracidad_porcentaje", "cantidad_upvotes", "cantidad_downvotes"}
        raw = payload.model_dump()
        sanitized: dict[str, Any] = {k: v for k, v in raw.items() if k in allowed and v is not None}

        # Si llegan contadores sin veracidad, recalcularla aquí
        up_in = sanitized.get("cantidad_upvotes")
        down_in = sanitized.get("cantidad_downvotes")
        ver_in = sanitized.get("veracidad_porcentaje")
        if ver_in is None and (up_in is not None or down_in is not None):
            # Obtener valores actuales para completar los que falten
            actual = await self.repo.get_by_id(reporte_id)
            if actual:
                up = int(up_in if up_in is not None else (actual.get("cantidad_upvotes") or 0))
                down = int(down_in if down_in is not None else (actual.get("cantidad_downvotes") or 0))
                total = up + down
                sanitized["veracidad_porcentaje"] = float((up / total) * 100.0) if total > 0 else 0.0

        updated = await self.repo.update_reporte(reporte_id, sanitized)
        if isinstance(updated, list):
            if not updated:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporte not found")
            updated = updated[0]

        return ReporteOut(**updated)

    async def delete_reporte(self, reporte_id: int) -> dict:
        deleted_count = await self.repo.delete_reporte(reporte_id)
        return {"deleted": deleted_count}
