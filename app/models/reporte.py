from pydantic import BaseModel, Field
from typing import Optional


class ReporteCreate(BaseModel):
    user_id: int
    titulo: str
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    direccion: Optional[str] = None
    distrito: Optional[str] = None  # Se obtiene automáticamente desde coordenadas
    estado: Optional[str] = None
    # Default veracity to 0 for new reports when not provided by client
    veracidad_porcentaje: Optional[float] = 0
    cantidad_upvotes: int = 0
    cantidad_downvotes: int = 0


class ReporteOut(ReporteCreate):
    id: Optional[int] = None
    created_at: Optional[str] = None
    # Override to accept NULLs from existing rows; default to 0 when missing
    cantidad_upvotes: Optional[int] = 0
    cantidad_downvotes: Optional[int] = 0


class ReporteUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    direccion: Optional[str] = None
    distrito: Optional[str] = None
    estado: Optional[str] = None
    veracidad_porcentaje: Optional[float] = None
    cantidad_upvotes: Optional[int] = None
    cantidad_downvotes: Optional[int] = None
