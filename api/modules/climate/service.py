from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlmodel import Session

from api.core.errors import ApiError
from api.modules.climate import repository
from api.modules.climate.models import ClimateHistory, Forecast
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
                for k in (
                    "tmin",
                    "tmax",
                    "tmean",
                    "pmm",
                    "et0",
                    "rh",
                    "sw",
                    "ws",
                    "sm_surface",
                    "sm_root",
                )
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


WEATHER_MAX_DAYS = 14
# The short forecast is refreshed at least daily; older data means the source failed.
WEATHER_STALE_AFTER = timedelta(hours=24)
LA_PAZ = ZoneInfo("America/La_Paz")


def _as_utc(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def short_forecast(session: Session, zone_id: str, dias: int = WEATHER_MAX_DAYS) -> dict[str, Any]:
    now = datetime.now(UTC)
    days = repository.weather_days(session, zone_id, now.astimezone(LA_PAZ).date(), dias)
    updated = max((_as_utc(d.actualizado_en) for d in days), default=None)
    return {
        "zone_id": zone_id,
        "actualizado_en": updated.astimezone(LA_PAZ).isoformat() if updated else None,
        "dias": [
            _present(
                {
                    "fecha": d.fecha.isoformat(),
                    "tmin": d.tmin,
                    "tmax": d.tmax,
                    "pmm": d.pmm,
                    "granizo": d.granizo,
                    "confianza": d.confianza,
                }
            )
            for d in days
        ],
        "fuente": sorted({d.fuente for d in days}),
        "desactualizado": updated is None or now - updated > WEATHER_STALE_AFTER,
    }


CLIMATOLOGY_YEARS = 30
FROST_C = 0.0
HISTORY_DEFAULT_DAYS = 28
HISTORY_MAX_DAYS = 366
# The valley IMERG series is loaded from the Late run, collection 07 (data/imerg/README.md).
IMERG_PRODUCT = {"pmm_producto": "late", "pmm_revision": "V07"}


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def _last_full_year(rows: list[ClimateHistory]) -> int:
    closed = [r.fecha.year for r in rows if (r.fecha.month, r.fecha.day) == (12, 31)]
    return max(closed) if closed else rows[-1].fecha.year


def _span(years: set[int]) -> str | None:
    return f"{min(years)}-{max(years)}" if years else None


def climatology(session: Session, zone_id: str) -> dict[str, Any]:
    rows = repository.history_rows(session, zone_id)
    if not rows:
        return {"zone_id": zone_id, "meses": [], "fuente": []}
    last = _last_full_year(rows)
    rows = [r for r in rows if last - CLIMATOLOGY_YEARS < r.fecha.year <= last]
    power_years = {r.fecha.year for r in rows if r.tmin is not None}
    imerg_years = {r.fecha.year for r in rows if r.pmm_sat is not None}
    months = []
    for mes in range(1, 13):
        days = [r for r in rows if r.fecha.month == mes]
        tmin = [r.tmin for r in days if r.tmin is not None]
        tmax = [r.tmax for r in days if r.tmax is not None]
        rain: dict[int, float] = {}
        for r in days:
            if r.pmm_sat is not None:
                rain[r.fecha.year] = rain.get(r.fecha.year, 0.0) + r.pmm_sat
        years = {r.fecha.year for r in days if r.tmin is not None}
        frost_years = {r.fecha.year for r in days if r.tmin is not None and r.tmin <= FROST_C}
        month = _present(
            {
                "mes": mes,
                "pmm_total": _mean(list(rain.values())),
                "tmin": _mean(tmin),
                "tmax": _mean(tmax),
                "p_helada": round(len(frost_years) / len(years), 2) if years else None,
            }
        )
        if len(month) > 1:
            months.append(month)
    return {
        "zone_id": zone_id,
        "periodo": _present({"power": _span(power_years), "imerg": _span(imerg_years)}),
        "meses": months,
        "fuente": [s for s, ys in (("nasa_power", power_years), ("nasa_imerg", imerg_years)) if ys],
    }


def _history_day(r: ClimateHistory) -> dict[str, Any]:
    day = {"fecha": r.fecha.isoformat(), "tmin": r.tmin, "tmax": r.tmax}
    if r.pmm_sat is not None:
        day |= {"fecha_utc": r.fecha.isoformat(), "pmm": round(r.pmm_sat, 1), **IMERG_PRODUCT}
    return _present(day)


def history(
    session: Session, zone_id: str, desde: date | None, hasta: date | None
) -> dict[str, Any]:
    hasta = hasta or repository.last_history_date(session, zone_id)
    if hasta is None:
        return {"dias": [], "fuente": []}
    desde = desde or hasta - timedelta(days=HISTORY_DEFAULT_DAYS - 1)
    if desde > hasta or (hasta - desde).days >= HISTORY_MAX_DAYS:
        raise ApiError(
            400, "invalid_request", f"desde..hasta must span 1 to {HISTORY_MAX_DAYS} days"
        )
    rows = repository.history_rows(session, zone_id, desde, hasta)
    fuente = [
        s
        for s, has in (
            ("nasa_imerg", any(r.pmm_sat is not None for r in rows)),
            ("nasa_power", any(r.tmin is not None for r in rows)),
        )
        if has
    ]
    return {"dias": [_history_day(r) for r in rows], "fuente": fuente}


def _require_zone(session: Session, zone_id: str) -> None:
    if not zones.zone_exists(session, zone_id):
        raise ApiError(404, "zone_not_found", f"zone_id {zone_id} does not exist")


def zone_climatology(session: Session, zone_id: str) -> dict[str, Any]:
    _require_zone(session, zone_id)
    return climatology(session, zone_id)


def zone_history(
    session: Session, zone_id: str, desde: date | None, hasta: date | None
) -> dict[str, Any]:
    _require_zone(session, zone_id)
    return history(session, zone_id, desde, hasta)


def zone_forecast(session: Session, zone_id: str, anio: int | None) -> dict[str, Any]:
    _require_zone(session, zone_id)
    return forecast(session, zone_id, anio)


def zone_weather(session: Session, zone_id: str, dias: int) -> dict[str, Any]:
    _require_zone(session, zone_id)
    if not 1 <= dias <= WEATHER_MAX_DAYS:
        raise ApiError(400, "invalid_request", f"dias must be 1 to {WEATHER_MAX_DAYS}")
    return short_forecast(session, zone_id, dias)
