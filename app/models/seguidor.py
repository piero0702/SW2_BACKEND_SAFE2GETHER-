from pydantic import BaseModel
from typing import Optional


class SeguidorCreate(BaseModel):
    seguidor_id: int
    seguido_id: int


class SeguidorOut(SeguidorCreate):
    id: Optional[int] = None
    created_at: Optional[str] = None


class SeguidorUpdate(BaseModel):
    seguidor_id: Optional[int] = None
    seguido_id: Optional[int] = None
