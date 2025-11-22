from fastapi import HTTPException, status
from typing import Any
from app.repositories.notas_comunidad_repository import NotasComunidadRepository
from app.repositories.reportes_repository import ReportesRepository
from app.models.nota_comunidad import NotaComunidadCreate, NotaComunidadOut, NotaComunidadUpdate


class NotasComunidadService:
    def __init__(self, repo: NotasComunidadRepository | None = None, reportes_repo: ReportesRepository | None = None):
        self.repo = repo or NotasComunidadRepository()
        self.reportes_repo = reportes_repo or ReportesRepository()

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
        allowed = {"reporte_id", "user_id", "nota", "es_veraz"}
        raw = payload.model_dump()
        sanitized = {k: v for k, v in raw.items() if k in allowed}
        # Validación básica
        nota_text = str(sanitized.get("nota") or "").strip()
        if not nota_text:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La nota no puede estar vacía")
        sanitized["nota"] = nota_text
        created = await self.repo.create_nota(sanitized)
        
        # Recalcular veracidad del reporte
        reporte_id = sanitized.get("reporte_id")
        if reporte_id:
            await self._recalcular_veracidad(reporte_id)
        
        return NotaComunidadOut(**created)

    async def get_nota(self, nota_id: int) -> NotaComunidadOut:
        row = await self.repo.get_by_id(nota_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota not found")
        return NotaComunidadOut(**row)

    async def update_nota(self, nota_id: int, payload: NotaComunidadUpdate | NotaComunidadCreate) -> NotaComunidadOut:
        # Obtener la nota antes de actualizar para saber su reporte_id
        nota_actual = await self.repo.get_by_id(nota_id)
        if not nota_actual:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota not found")
        
        allowed = {"reporte_id", "user_id", "nota", "es_veraz"}
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

        # Recalcular veracidad del reporte si cambió es_veraz
        if "es_veraz" in sanitized:
            reporte_id = nota_actual.get("reporte_id")
            if reporte_id:
                await self._recalcular_veracidad(reporte_id)

        return NotaComunidadOut(**updated)

    async def delete_nota(self, nota_id: int) -> dict:
        # Obtener la nota antes de eliminar para saber su reporte_id
        nota = await self.repo.get_by_id(nota_id)
        reporte_id = nota.get("reporte_id") if nota else None
        
        deleted_count = await self.repo.delete_nota(nota_id)
        
        # Recalcular veracidad del reporte
        if reporte_id:
            await self._recalcular_veracidad(reporte_id)
        
        return {"deleted": deleted_count}
    
    async def _recalcular_veracidad(self, reporte_id: int) -> None:
        """
        Recalcula el porcentaje de veracidad y los contadores de upvotes/downvotes
        considerando tanto las reacciones como las notas de comunidad.
        
        Lógica:
        - Notas con es_veraz=True se suman como upvotes
        - Notas con es_veraz=False se suman como downvotes
        - Notas con es_veraz=null no afectan los contadores
        
        Los contadores cantidad_upvotes y cantidad_downvotes en la tabla Reportes
        incluyen tanto las reacciones como las notas de comunidad.
        """
        # Obtener reacciones del reporte (upvote/downvote)
        from app.repositories.reacciones_repository import ReaccionesRepository
        reacciones_repo = ReaccionesRepository()
        
        reacciones = await reacciones_repo.list_by_reporte(reporte_id)
        
        # Contar reacciones
        upvotes_reacciones = sum(1 for r in reacciones if r.get("tipo", "").lower() == "upvote")
        downvotes_reacciones = sum(1 for r in reacciones if r.get("tipo", "").lower() == "downvote")
        
        # Obtener notas del reporte
        notas = await self.repo.list_by_reporte(reporte_id)
        
        # Contar notas veraces y falsas (ignorar las neutrales/null)
        notas_veraces = sum(1 for n in notas if n.get("es_veraz") is True)
        notas_falsas = sum(1 for n in notas if n.get("es_veraz") is False)
        
        # Calcular totales: reacciones + notas
        total_upvotes = upvotes_reacciones + notas_veraces
        total_downvotes = downvotes_reacciones + notas_falsas
        
        # Calcular veracidad
        total = total_upvotes + total_downvotes
        if total > 0:
            veracidad_final = (total_upvotes / total) * 100
        else:
            # Sin datos, valor neutral
            veracidad_final = 50.0
        
        # Determinar estado basado en veracidad
        if veracidad_final >= 70:
            estado = "Verificado"
        elif veracidad_final >= 40:
            estado = "Activo"
        else:
            estado = "Dudoso"
        
        # Actualizar el reporte con los nuevos contadores y veracidad
        await self.reportes_repo.update_reporte(reporte_id, {
            "cantidad_upvotes": total_upvotes,
            "cantidad_downvotes": total_downvotes,
            "veracidad_porcentaje": round(veracidad_final, 2),
            "estado": estado
        })
