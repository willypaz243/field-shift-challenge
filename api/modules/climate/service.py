import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session

from api.core.errors import ApiError
from api.modules.climate import repository
from api.modules.zones import service as zones

FORECAST_SOURCES = ["nasa_power", "nasa_imerg", "nasa_smap"]
MODEL_TYPE = "fourier_tendencia"
METRICS_PATH = Path(__file__).resolve().parents[3] / "data" / "model" / "metrics_backtest.json"

_model_info_cache: dict[str, Any] | None = None


def _model_info() -> dict[str, Any]:
    """Contract §2.3 `modelo` block: type + holdout MAE from the pipeline metrics."""
    global _model_info_cache
    if _model_info_cache is None:
        backtest: dict[str, Any] | None = None
        if METRICS_PATH.exists():
            metrics = json.loads(METRICS_PATH.read_text())
            mae = {
                m["variable"]: m["mae"]
                for m in metrics.get("metrics", [])
                if m["variable"] in ("tmin", "pmm")
            }
            parts = str(metrics.get("holdout", "")).split("→")
            if len(parts) == 2 and mae:
                backtest = {"periodo": f"{parts[0].strip()[:4]}-{parts[1].strip()[:4]}", "mae": mae}
        _model_info_cache = {"tipo": MODEL_TYPE}
        if backtest is not None:
            _model_info_cache["backtest"] = backtest
    return _model_info_cache


def _day(f) -> dict[str, Any]:
    return {
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
        "incert_min": {"tmin": f.tmin_min, "pmm": f.pmm_min},
        "incert_max": {"tmin": f.tmin_max, "pmm": f.pmm_max},
    }


def forecast(session: Session, zone_id: str) -> dict[str, Any]:
    if not zones.zone_exists(session, zone_id):
        raise ApiError(404, "zone_not_found", f"zone_id {zone_id} does not exist")
    days = repository.forecast_days(session, zone_id)
    result: dict[str, Any] = {
        "zone_id": zone_id,
        "anio": days[0].anio if days else datetime.now().year + 1,
        "dias": [_day(f) for f in days],
        "fuente": FORECAST_SOURCES,
        "modelo": _model_info(),
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
