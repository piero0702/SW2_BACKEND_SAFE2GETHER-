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
    estado: Optional[str] = None
    veracidad_porcentaje: Optional[float] = None


class ReporteOut(ReporteCreate):
    id: Optional[int] = None
    created_at: Optional[str] = None


class ReporteUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    direccion: Optional[str] = None
    estado: Optional[str] = None
    veracidad_porcentaje: Optional[float] = None
