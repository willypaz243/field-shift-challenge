from datetime import datetime

from sqlalchemy import Column, LargeBinary
from sqlmodel import Field, SQLModel

from api.core.models import utcnow


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: int | None = Field(default=None, primary_key=True)
    idempotency_key: str = Field(unique=True)
    tipo: str
    zone_id: str = Field(foreign_key="zones.id")
    lat: float | None = None
    lon: float | None = None
    ocurrido_en: datetime
    creado_en: datetime = Field(default_factory=utcnow)
    foto: bytes | None = Field(default=None, sa_column=Column(LargeBinary))
    audio: bytes | None = Field(default=None, sa_column=Column(LargeBinary))
