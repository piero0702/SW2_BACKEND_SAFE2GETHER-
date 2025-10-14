from pydantic import BaseModel, Field
from typing import Optional


class AdjuntoCreate(BaseModel):
    reporte_id: int
    url: str
    tipo: str
  

class AdjuntoOut(AdjuntoCreate):
    id: Optional[int] = None
    created_at: Optional[str] = None


class AdjuntoUpdate(BaseModel):
    url: str = None
    tipo: Optional[str] = None
