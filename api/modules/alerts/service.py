from datetime import date, datetime, timedelta
from typing import Any

from sqlmodel import Session

from api.core.errors import ApiError
from api.modules.alerts import repository
from api.modules.climate import service as climate
from api.modules.water import service as water
from api.modules.zones import service as zones

FROST_C = 0.0
# The reservoir level is loaded weekly; an older reading no longer describes the water available.
RESERVOIR_MAX_AGE = timedelta(days=30)


def zone_history(session: Session, zone_id: str) -> list[dict[str, Any]]:
    rows = (
        {
            "fecha": e.fecha.isoformat(),
            "tipo": e.tipo,
            "descripcion": e.descripcion,
            "fuente": e.fuente,
        }
        for e in repository.events_for_zone(session, zone_id)
    )
    return [{k: v for k, v in row.items() if v is not None} for row in rows]


def _weather_alerts(session: Session, zone_id: str) -> list[dict[str, Any]]:
    found = []
    for day in climate.short_forecast(session, zone_id)["dias"]:
        fecha = date.fromisoformat(day["fecha"])
        common = {
            "fecha_evento": day["fecha"],
            "confianza": day["confianza"],
            "volver_a_avisar": (fecha - timedelta(days=1)).isoformat(),
        }
        if day["tmin"] <= FROST_C:
            found.append(
                {
                    "id": f"helada-{day['fecha']}",
                    "tipo": "helada",
                    **common,
                    "momento": "madrugada",
                    "valor": {"tmin": day["tmin"]},
                    "regla": {"id": "helada-tmin-0"},
                }
            )
        if day.get("granizo"):
            found.append(
                {
                    "id": f"granizo-{day['fecha']}",
                    "tipo": "granizo",
                    **common,
                    "regla": {"id": "granizo-pronostico"},
                }
            )
    return found


def _reservoir_alert(session: Session, today: date) -> dict[str, Any] | None:
    reservoir = water.la_angostura(session)
    if reservoir is None or reservoir.get("estado") not in ("bajo", "critico"):
        return None
    updated = reservoir.get("actualizado_en")
    if updated is None or today - datetime.fromisoformat(updated).date() > RESERVOIR_MAX_AGE:
        return None
    return {
        "id": "represa_baja",
        "tipo": "represa_baja",
        "valor": {"nivel_pct": reservoir["nivel_pct"]},
    }


def active_alerts(session: Session, zone_id: str) -> list[dict[str, Any]]:
    today = datetime.now(climate.LA_PAZ).date()
    found = sorted(_weather_alerts(session, zone_id), key=lambda a: a["fecha_evento"])
    reservoir = _reservoir_alert(session, today)
    return found + ([reservoir] if reservoir else [])


def zone_alerts(session: Session, zone_id: str) -> dict[str, Any]:
    if not zones.zone_exists(session, zone_id):
        raise ApiError(404, "zone_not_found", f"zone_id {zone_id} does not exist")
    return {
        "actualizado_en": datetime.now(climate.LA_PAZ).isoformat(timespec="seconds"),
        "alertas": active_alerts(session, zone_id),
    }
