from fastapi import HTTPException, status
from typing import Any
from app.repositories.reacciones_repository import ReaccionesRepository
from app.repositories.reportes_repository import ReportesRepository
from app.models.reaccion import ReaccionCreate, ReaccionOut, ReaccionUpdate


class ReaccionesService:
    def __init__(self, repo: ReaccionesRepository | None = None, reportes_repo: ReportesRepository | None = None):
        self.repo = repo or ReaccionesRepository()
        self.reportes_repo = reportes_repo or ReportesRepository()

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
        # Ajustar contadores en Reportes y recalcular veracidad
        try:
            reporte_id = created.get("reporte_id") if isinstance(created, dict) else sanitized.get("reporte_id")
            tipo = created.get("tipo") if isinstance(created, dict) else sanitized.get("tipo")
            if reporte_id is not None and tipo in ("upvote", "downvote"):
                await self._apply_reaction_delta(reporte_id=reporte_id, old_tipo=None, new_tipo=tipo)
        except Exception:
            # No romper la creación de la reacción si falla el ajuste de contadores
            pass
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

        # Obtener estado previo para calcular diferencias
        prev = await self.repo.get_by_id(reaccion_id)
        updated = await self.repo.update_reaccion(reaccion_id, sanitized)
        if isinstance(updated, list):
            if not updated:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reaccion not found")
            updated = updated[0]
        # Ajustar contadores si cambió el tipo o el reporte al que pertenece
        try:
            old_tipo = prev.get("tipo") if isinstance(prev, dict) else None
            new_tipo = updated.get("tipo") if isinstance(updated, dict) else sanitized.get("tipo")
            old_reporte = prev.get("reporte_id") if isinstance(prev, dict) else None
            new_reporte = updated.get("reporte_id") if isinstance(updated, dict) else sanitized.get("reporte_id") or old_reporte

            if new_reporte is not None and (old_tipo != new_tipo or old_reporte != new_reporte):
                # Si cambió de reporte, revertir en el viejo y aplicar en el nuevo
                if old_reporte is not None and old_reporte != new_reporte and old_tipo in ("upvote", "downvote"):
                    await self._apply_reaction_delta(reporte_id=old_reporte, old_tipo=old_tipo, new_tipo=None)
                if new_tipo in ("upvote", "downvote"):
                    await self._apply_reaction_delta(reporte_id=new_reporte, old_tipo=old_tipo if old_reporte == new_reporte else None, new_tipo=new_tipo)
        except Exception:
            pass

        return ReaccionOut(**updated)

    async def delete_reaccion(self, reaccion_id: int) -> dict:
        # Leer reacción antes de eliminar para ajustar contadores
        prev = await self.repo.get_by_id(reaccion_id)
        deleted_count = await self.repo.delete_reaccion(reaccion_id)
        try:
            if deleted_count and isinstance(prev, dict):
                reporte_id = prev.get("reporte_id")
                old_tipo = prev.get("tipo")
                if reporte_id is not None and old_tipo in ("upvote", "downvote"):
                    await self._apply_reaction_delta(reporte_id=reporte_id, old_tipo=old_tipo, new_tipo=None)
        except Exception:
            pass
        return {"deleted": deleted_count}

    async def _apply_reaction_delta(self, *, reporte_id: int, old_tipo: str | None, new_tipo: str | None) -> None:
        """Aplica deltas a upvotes/downvotes según el cambio de reacción y recalcula veracidad.

        Reglas:
        - None -> upvote: up +1
        - None -> downvote: down +1
        - upvote -> None: up -1
        - downvote -> None: down -1
        - upvote -> downvote: up -1, down +1
        - downvote -> upvote: down -1, up +1
        """
        # Obtener contadores actuales del reporte
        reporte = await self.reportes_repo.get_by_id(reporte_id)
        if not reporte:
            return
        up = int(reporte.get("cantidad_upvotes") or 0)
        down = int(reporte.get("cantidad_downvotes") or 0)

        # Calcular deltas
        delta_up = 0
        delta_down = 0
        if old_tipo is None and new_tipo == "upvote":
            delta_up = 1
        elif old_tipo is None and new_tipo == "downvote":
            delta_down = 1
        elif old_tipo == "upvote" and new_tipo is None:
            delta_up = -1
        elif old_tipo == "downvote" and new_tipo is None:
            delta_down = -1
        elif old_tipo == "upvote" and new_tipo == "downvote":
            delta_up = -1
            delta_down = 1
        elif old_tipo == "downvote" and new_tipo == "upvote":
            delta_up = 1
            delta_down = -1

        new_up = max(0, up + delta_up)
        new_down = max(0, down + delta_down)
        total = new_up + new_down
        veracidad = float((new_up / total) * 100.0) if total > 0 else 0.0

        # Aplicar regla de estado en función de la veracidad
        payload = {
            "cantidad_upvotes": new_up,
            "cantidad_downvotes": new_down,
            "veracidad_porcentaje": veracidad,
        }
        try:
            if veracidad < 33.0:
                payload["estado"] = "Falso"
            else:
                payload["estado"] = "Activo"
        except Exception:
            pass

        await self.reportes_repo.update_reporte(
            reporte_id,
            payload,
        )
