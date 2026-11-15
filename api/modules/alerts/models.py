from datetime import date

from sqlmodel import Field, SQLModel


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: int | None = Field(default=None, primary_key=True)
    tipo: str
    fecha: date
    zone_id: str | None = None
    descripcion: str | None = None
    fuente: str | None = None
