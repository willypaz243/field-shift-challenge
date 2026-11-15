from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import JSON, Column, LargeBinary
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Zone(SQLModel, table=True):
    __tablename__ = "zones"

    id: str = Field(primary_key=True)
    nombre: str
    comuna: str
    distrito: int | None = None
    lat: float
    lon: float
    elev_m: float | None = None
    pendiente: float | None = None
    es_agricola: bool = True
    cerca_drenaje: int | None = None
    altitud_alta: bool = False


class ClimateHistory(SQLModel, table=True):
    __tablename__ = "climate_history"

    zone_id: str = Field(foreign_key="zones.id", primary_key=True)
    fecha: date = Field(primary_key=True)
    tmin: float | None = None
    tmax: float | None = None
    tmean: float | None = None
    t2mdew: float | None = None
    pmm: float | None = None
    rh: float | None = None
    ws: float | None = None
    ps: float | None = None
    sw: float | None = None
    sw_clear: float | None = None
    lw: float | None = None
    sm_surface: float | None = None
    sm_root: float | None = None


class Crop(SQLModel, table=True):
    __tablename__ = "crops"

    id: str = Field(primary_key=True)
    nombre: str
    t_opt_min: float | None = None
    t_opt_max: float | None = None
    tol_helada: str | None = None
    demanda_agua: str | None = None
    ciclo_min_dias: int | None = None
    ciclo_max_dias: int | None = None
    fix_n: bool = False
    mercado: str | None = None
    foto_url: str | None = None


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: int | None = Field(default=None, primary_key=True)
    tipo: str
    fecha: date
    zone_id: str | None = Field(default=None, foreign_key="zones.id")
    descripcion: str | None = None
    fuente: str | None = None


class Forecast(SQLModel, table=True):
    __tablename__ = "forecasts"

    zone_id: str = Field(foreign_key="zones.id", primary_key=True)
    fecha: date = Field(primary_key=True)
    anio: int
    tmin: float | None = None
    tmax: float | None = None
    tmean: float | None = None
    pmm: float | None = None
    rh: float | None = None
    sw: float | None = None
    ws: float | None = None
    sm_surface: float | None = None
    sm_root: float | None = None
    incert_min: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON)
    )
    incert_max: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON)
    )
    creado_en: datetime = Field(default_factory=_utcnow)


class SyncVersion(SQLModel, table=True):
    __tablename__ = "sync_version"

    id: int | None = Field(default=None, primary_key=True)
    creado_en: datetime = Field(default_factory=_utcnow)
    hash: str


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: int | None = Field(default=None, primary_key=True)
    idempotency_key: str = Field(unique=True)
    tipo: str
    zone_id: str = Field(foreign_key="zones.id")
    lat: float
    lon: float
    ocurrido_en: datetime
    creado_en: datetime = Field(default_factory=_utcnow)
    foto: bytes | None = Field(default=None, sa_column=Column(LargeBinary))
    audio: bytes | None = Field(default=None, sa_column=Column(LargeBinary))


class Feedback(SQLModel, table=True):
    __tablename__ = "feedback"

    id: int | None = Field(default=None, primary_key=True)
    zone_id: str = Field(foreign_key="zones.id")
    crop_id: str = Field(foreign_key="crops.id")
    siembra: date
    cosecha: date
    resultado: str
    creado_en: datetime = Field(default_factory=_utcnow)
