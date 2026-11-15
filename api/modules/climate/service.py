from datetime import datetime
from typing import Any

from sqlmodel import Session

from api.core.errors import ApiError
from api.modules.climate import repository
from api.modules.climate.models import Forecast
from api.modules.zones import service as zones

FORECAST_SOURCES = ["nasa_power", "nasa_imerg", "nasa_smap"]


def _present(values: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in values.items() if v is not None}


def _day(f: Forecast) -> dict[str, Any]:
    return _present(
        {
            "fecha": f.fecha.isoformat(),
            **{
                k: getattr(f, k)
                for k in ("tmin", "tmax", "tmean", "pmm", "rh", "sw", "ws", "sm_surface", "sm_root")
            },
            "incert_min": _present({"tmin": f.tmin_min, "pmm": f.pmm_min}) or None,
            "incert_max": _present({"tmin": f.tmin_max, "pmm": f.pmm_max}) or None,
        }
    )


def forecast(session: Session, zone_id: str, anio: int | None = None) -> dict[str, Any]:
    days = repository.forecast_days(session, zone_id, anio)
    result = {
        "zone_id": zone_id,
        "anio": anio or (days[0].anio if days else datetime.now().year + 1),
        "dias": [_day(f) for f in days],
        "fuente": FORECAST_SOURCES,
    }
    if days:
        result["creado_en"] = days[0].creado_en.isoformat()
    return result


def short_forecast(zone_id: str, updated: datetime | None) -> dict[str, Any]:
    return {
        "zone_id": zone_id,
        "actualizado_en": updated.isoformat() if updated else None,
        "dias": [],
        "fuente": [],
    }


def climatology(zone_id: str) -> dict[str, Any]:
    return {"zone_id": zone_id, "meses": [], "fuente": []}


def zone_forecast(session: Session, zone_id: str, anio: int | None) -> dict[str, Any]:
    if not zones.zone_exists(session, zone_id):
        raise ApiError(404, "zone_not_found", f"zone_id {zone_id} does not exist")
    return forecast(session, zone_id, anio)
