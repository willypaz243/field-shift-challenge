"""Response schemas for the climate module (API-CONTRACT §2.3)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class ForecastDay(BaseModel):
    fecha: date
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
    incert_min: dict[str, float | None] | None = None
    incert_max: dict[str, float | None] | None = None


class ForecastResponse(BaseModel):
    zone_id: str
    anio: int
    dias: list[ForecastDay]
    fuente: list[str]
    modelo: dict[str, Any] | None = None
    creado_en: datetime | None = None
