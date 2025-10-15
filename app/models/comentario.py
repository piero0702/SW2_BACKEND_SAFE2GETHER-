from pydantic import BaseModel
from typing import Optional


class ComentarioCreate(BaseModel):
    reporte_id: int
    user_id: int
    mensaje: str


class ComentarioOut(ComentarioCreate):
    id: Optional[int] = None
    created_at: Optional[str] = None


class ComentarioUpdate(BaseModel):
    reporte_id: Optional[int] = None
    user_id: Optional[int] = None
    mensaje: Optional[str] = None
