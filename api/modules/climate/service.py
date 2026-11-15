from datetime import datetime

from sqlmodel import Session

from api.modules.climate import repository

FORECAST_SOURCES = ["nasa_power", "nasa_imerg", "nasa_smap"]


def _day(f) -> dict:
    return {
        "fecha": f.fecha.isoformat(),
        **{
            k: getattr(f, k)
            for k in ("tmin", "tmax", "tmean", "pmm", "rh", "sw", "ws", "sm_surface", "sm_root")
        },
        "incert_min": {"tmin": f.tmin_min, "pmm": f.pmm_min},
        "incert_max": {"tmin": f.tmin_max, "pmm": f.pmm_max},
    }


def forecast(session: Session, zone_id: str) -> dict:
    days = repository.forecast_days(session, zone_id)
    result = {
        "zone_id": zone_id,
        "anio": days[0].anio if days else datetime.now().year + 1,
        "dias": [_day(f) for f in days],
        "fuente": FORECAST_SOURCES,
    }
    if days:
        result["creado_en"] = days[0].creado_en.isoformat()
    return result


def short_forecast(zone_id: str, updated: datetime | None) -> dict:
    return {
        "zone_id": zone_id,
        "actualizado_en": updated.isoformat() if updated else None,
        "dias": [],
        "fuente": [],
    }


def climatology(zone_id: str) -> dict:
    return {"zone_id": zone_id, "meses": [], "fuente": []}
