from datetime import datetime

from pydantic import BaseModel


class ZoneOut(BaseModel):
    id: str
    nombre: str | None
    comuna: str | None
    distrito: int | None
    lat: float
    lon: float
    elev_m: float | None
    pendiente: float | None
    es_agricola: bool
    cerca_drenaje: int | None
    altitud_alta: bool


class ZonesResponse(BaseModel):
    actualizado_en: datetime | None
    zones: list[ZoneOut]
    fuente: list[str]
