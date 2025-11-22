from pydantic import BaseModel
from typing import Optional


class NotaComunidadCreate(BaseModel):
    reporte_id: int
    user_id: int
    nota: str
    es_veraz: Optional[bool] = None  # True = veraz, False = falso, None = neutral


class NotaComunidadOut(NotaComunidadCreate):
    id: Optional[int] = None
    created_at: Optional[str] = None


class NotaComunidadUpdate(BaseModel):
    reporte_id: Optional[int] = None
    user_id: Optional[int] = None
    nota: Optional[str] = None
    es_veraz: Optional[bool] = None
