from pydantic import BaseModel
from typing import Optional


class ReaccionCreate(BaseModel):
    reporte_id: int
    user_id: int
    tipo: str


class ReaccionOut(ReaccionCreate):
    id: Optional[int] = None
    created_at: Optional[str] = None


class ReaccionUpdate(BaseModel):
    reporte_id: Optional[int] = None
    user_id: Optional[int] = None
    tipo: Optional[str] = None
