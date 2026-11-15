import hashlib
import json
from typing import Any

from sqlmodel import Session

from api.modules.alerts import service as alerts
from api.modules.climate import service as climate
from api.modules.crops import service as crops
from api.modules.rotations import service as rotations
from api.modules.water import service as water
from api.modules.zones import service as zones


def current_version(session: Session) -> int:
    return zones.last_load_version(session)[0]


def ensure_zone(session: Session, zone_id: str) -> None:
    zones.get_zone(session, zone_id)


def package(session: Session, zone_id: str) -> dict[str, Any]:
    zone = zones.get_zone(session, zone_id)
    version, updated = zones.last_load_version(session)
    sections = {
        "zone": zone.model_dump(exclude_none=True),
        "crops": crops.catalog(),
        "forecast": climate.forecast(session, zone_id),
        "corto_plazo": climate.short_forecast(zone_id, updated),
        "climatologia": climate.climatology(zone_id),
        "alertas": alerts.active_alerts(session, zone_id),
        "rotaciones": rotations.catalog(),
        "represa": water.la_angostura(session),
        "historial_zona": alerts.zone_history(session, zone_id),
    }
    digest = hashlib.sha256(json.dumps(sections, sort_keys=True, default=str).encode()).hexdigest()
    return {"sync_version": version, "hash": f"sha256:{digest}", **sections}
