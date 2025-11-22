from pydantic import BaseModel
from typing import Optional


class AreaInteresCreate(BaseModel):
    user_id: int
    nombre: str
    lat: float
    lon: float
    radio_metros: Optional[int] = 1000  # Radio por defecto: 1km
    frecuencia_notificacion: Optional[str] = "semanal"  # "diario" o "semanal"
    activo: Optional[bool] = True


class AreaInteresOut(AreaInteresCreate):
    id: Optional[int] = None
    created_at: Optional[str] = None
    ultima_notificacion: Optional[str] = None  # Timestamp de última notificación enviada


class AreaInteresUpdate(BaseModel):
    nombre: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    radio_metros: Optional[int] = None
    frecuencia_notificacion: Optional[str] = None
    activo: Optional[bool] = None
    ultima_notificacion: Optional[str] = None
