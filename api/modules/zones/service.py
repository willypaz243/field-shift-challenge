from datetime import datetime

from sqlmodel import Session

from api.core.errors import ApiError
from api.modules.zones import repository
from api.modules.zones.models import Zone
from api.modules.zones.schemas import ZoneOut, ZonesResponse

SOURCES = ["gamc_wms", "srtm"]


def zone_exists(session: Session, zone_id: str) -> bool:
    return repository.get_zone(session, zone_id) is not None


def _district_number(distrito: str | None) -> int | None:
    digits = "".join(ch for ch in distrito or "" if ch.isdigit())
    return int(digits) if digits else None


def _to_out(zone: Zone) -> ZoneOut:
    return ZoneOut(**{**zone.model_dump(), "distrito": _district_number(zone.distrito)})


def list_zones(session: Session) -> ZonesResponse:
    last = repository.last_load(session)
    return ZonesResponse(
        actualizado_en=last.creado_en if last else None,
        zones=[_to_out(z) for z in repository.list_zones(session)],
        fuente=SOURCES,
    )


def get_zone(session: Session, zone_id: str) -> ZoneOut:
    zone = repository.get_zone(session, zone_id)
    if zone is None:
        raise ApiError(404, "zone_not_found", f"zone_id {zone_id} does not exist")
    return _to_out(zone)


def last_load_version(session: Session) -> tuple[int, datetime | None]:
    last = repository.last_load(session)
    return (last.id, last.creado_en) if last else (0, None)
