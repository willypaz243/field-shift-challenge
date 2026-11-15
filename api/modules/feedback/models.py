from datetime import date, datetime

from sqlmodel import Field, SQLModel

from api.core.models import utcnow


class Feedback(SQLModel, table=True):
    __tablename__ = "feedback"

    id: int | None = Field(default=None, primary_key=True)
    idempotency_key: str = Field(unique=True)
    zone_id: str = Field(foreign_key="zones.id")
    crop_id: str = Field(foreign_key="crops.id")
    siembra: date | None = None
    cosecha: date
    resultado: str
    creado_en: datetime = Field(default_factory=utcnow)


class Plan(SQLModel, table=True):
    __tablename__ = "plans"

    id: int | None = Field(default=None, primary_key=True)
    idempotency_key: str = Field(unique=True)
    zone_id: str = Field(foreign_key="zones.id")
    rotacion_id: str
    siembra: date
    creado_en: datetime = Field(default_factory=utcnow)
