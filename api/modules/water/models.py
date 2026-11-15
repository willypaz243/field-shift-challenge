from datetime import date

from sqlmodel import Field, SQLModel


class Reservoir(SQLModel, table=True):
    __tablename__ = "reservoir"

    id: str = Field(primary_key=True)
    nombre: str
    nivel_pct: float | None = None
    volumen_hm3: float | None = None
    estado: str | None = None
    actualizado_en: date | None = None
