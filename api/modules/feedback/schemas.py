from datetime import date

from pydantic import BaseModel


class FeedbackIn(BaseModel):
    zone_id: str
    crop_id: str
    siembra: date | None = None
    cosecha: date
    resultado: str


class Created(BaseModel):
    id: str
