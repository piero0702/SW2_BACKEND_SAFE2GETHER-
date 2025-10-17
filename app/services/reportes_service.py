from fastapi import HTTPException, status
from typing import Any
from app.repositories.reportes_repository import ReportesRepository
from app.repositories.users_repository import UsersRepository
from app.services.email_service import send_report_confirmation_email
from app.models.reporte import ReporteCreate, ReporteOut, ReporteUpdate


class ReportesService:
    def __init__(self, repo: ReportesRepository | None = None, users_repo: UsersRepository | None = None):
        self.repo = repo or ReportesRepository()
        self.users_repo = users_repo or UsersRepository()

    async def list_reportes(self, *, limit: int | None = 20, offset: int | None = 0, order: str | None = "created_at.desc") -> list[ReporteOut]:
        rows = await self.repo.list_reportes(limit=limit, offset=offset, order=order)
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
        # Default estado to "Activo" if not provided or empty
        estado_val = sanitized.get("estado")
        if estado_val is None or (isinstance(estado_val, str) and not estado_val.strip()):
            sanitized["estado"] = "Activo"
        # Regla: estado basado en veracidad (<33 => Falso, >=33 => Activo)
        try:
            v = sanitized.get("veracidad_porcentaje")
            if v is not None:
                if float(v) < 33.0:
                    sanitized["estado"] = "Falso"
                else:
                    sanitized["estado"] = "Activo"
        except Exception:
            pass
        created = await self.repo.create_reporte(sanitized)

        # Enviar email de confirmación al usuario si es posible
        try:
            user_id = sanitized.get("user_id")
            if user_id is not None:
                user = await self.users_repo.get_by_id(int(user_id))
                if user and user.get("email"):
                    email = user["email"]
                    username = user.get("user", "Usuario")
                    rid = created.get("id")
                    if rid is not None:
                        try:
                            rid = int(rid)
                        except Exception:
                            rid = None
                    # Solo enviar si tenemos un ID válido
                    if isinstance(rid, int):
                        await send_report_confirmation_email(
                            to_email=email,
                            username=username,
                            reporte_id=rid,
                            titulo=str(created.get("titulo") or sanitized.get("titulo") or ""),
                            categoria=(created.get("categoria") or sanitized.get("categoria")),
                            direccion=(created.get("direccion") or sanitized.get("direccion")),
                        )
        except Exception as e:
            # No bloquear creación por errores de email
            print(f"⚠️ No se pudo enviar email de confirmación: {e}")

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

        # Regla: estado basado en veracidad (<33 => Falso, >=33 => Activo)
        try:
            v = sanitized.get("veracidad_porcentaje")
            if v is not None:
                if float(v) < 33.0:
                    sanitized["estado"] = "Falso"
                else:
                    sanitized["estado"] = "Activo"
        except Exception:
            pass

        updated = await self.repo.update_reporte(reporte_id, sanitized)
        if isinstance(updated, list):
            if not updated:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporte not found")
            updated = updated[0]

        return ReporteOut(**updated)

    async def delete_reporte(self, reporte_id: int) -> dict:
        deleted_count = await self.repo.delete_reporte(reporte_id)
        return {"deleted": deleted_count}
