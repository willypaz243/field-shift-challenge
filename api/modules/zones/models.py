from sqlmodel import Field, SQLModel


class Zone(SQLModel, table=True):
    __tablename__ = "zones"

    id: str = Field(primary_key=True)
    nombre: str | None = None
    comuna: str | None = None
    distrito: str | None = None
    lat: float
    lon: float
    elev_m: float | None = None
    pendiente: float | None = None
    es_agricola: bool = True
    cerca_drenaje: int | None = None
    altitud_alta: bool = False
