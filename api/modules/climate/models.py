from datetime import date, datetime

from sqlmodel import Field, SQLModel

from api.core.models import utcnow


class ClimateHistory(SQLModel, table=True):
    __tablename__ = "climate_history"

    zone_id: str = Field(foreign_key="zones.id", primary_key=True)
    fecha: date = Field(primary_key=True, index=True)
    tmin: float | None = None
    tmax: float | None = None
    tmean: float | None = None
    pmm: float | None = None
    rh: float | None = None
    sw: float | None = None
    ws: float | None = None
    et0: float | None = None
    sm_surface: float | None = None
    sm_root: float | None = None
    pmm_sat: float | None = None
    t2mdew: float | None = None
    ps: float | None = None
    sw_clear: float | None = None
    lw: float | None = None


class Forecast(SQLModel, table=True):
    __tablename__ = "forecasts"

    zone_id: str = Field(foreign_key="zones.id", primary_key=True)
    fecha: date = Field(primary_key=True)
    anio: int
    tmin: float | None = None
    tmax: float | None = None
    tmean: float | None = None
    pmm: float | None = None
    et0: float | None = None
    rh: float | None = None
    sw: float | None = None
    ws: float | None = None
    sm_surface: float | None = None
    sm_root: float | None = None
    tmin_min: float | None = None
    tmin_max: float | None = None
    pmm_min: float | None = None
    pmm_max: float | None = None
    creado_en: datetime = Field(default_factory=utcnow)
