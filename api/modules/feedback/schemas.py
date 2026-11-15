from datetime import date
from typing import Literal

from pydantic import BaseModel


class FeedbackIn(BaseModel):
    zone_id: str
    crop_id: str
    siembra: date | None = None
    cosecha: date
    resultado: Literal["buena", "regular", "mala"]


class PlanIn(BaseModel):
    zone_id: str
    rotacion_id: str
    siembra: date


class Created(BaseModel):
    id: str
