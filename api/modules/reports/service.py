import math
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlmodel import Session

from api.core.errors import ApiError
from api.modules.alerts import service as alerts
from api.modules.reports import repository
from api.modules.reports.models import Report
from api.modules.zones import service as zones

TIPOS = {"sin_agua", "helada", "granizo", "inundacion", "plaga"}
MAX_FOTO_BYTES = 300_000
# About 60 s of compressed voice.
MAX_AUDIO_BYTES = 1_000_000
WEEK = timedelta(days=7)
# Cells of 0.01 deg (~1 km) group neighbours without pointing at a single plot.
CELL_DEG = 0.01
MIN_REPORTS_PER_CELL = 3
DIRECTIONS = ["este", "noreste", "norte", "noroeste", "oeste", "suroeste", "sur", "sureste"]
LA_PAZ = ZoneInfo("America/La_Paz")


class DuplicateKey(Exception):
    def __init__(self, response: dict[str, Any]) -> None:
        super().__init__(response["id"])
        self.response = response


def _invalid(message: str) -> ApiError:
    return ApiError(400, "invalid_request", message)


def _number(fields: dict[str, str], name: str) -> float | None:
    value = fields.get(name, "").strip()
    if not value:
        return None
    try:
        return round(float(value), 3)
    except ValueError:
        raise _invalid(f"{name} must be a number") from None


def _moment(value: str) -> datetime:
    try:
        moment = datetime.fromisoformat(value.strip())
    except ValueError:
        raise _invalid("ocurrido_en must be an ISO 8601 date-time") from None
    return (moment if moment.tzinfo else moment.replace(tzinfo=LA_PAZ)).astimezone(UTC)


def _attachment(files: dict[str, tuple[str, bytes]], name: str, limit: int) -> bytes | None:
    if name not in files:
        return None
    content_type, data = files[name]
    if name == "foto" and content_type != "image/jpeg":
        raise _invalid("foto must be image/jpeg")
    if len(data) > limit:
        raise _invalid(f"{name} larger than {limit} bytes")
    return data


def _as_utc(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def _response(session: Session, report: Report) -> dict[str, Any]:
    since = datetime.now(UTC) - WEEK
    neighbours = [
        r
        for r in repository.recent(session, report.zone_id, report.tipo, since)
        if r.id != report.id
    ]
    return {"id": f"rep-{report.id}", "vecinos_mismo_tipo_semana": len(neighbours)}


def create_report(
    session: Session, key: str, fields: dict[str, str], files: dict[str, tuple[str, bytes]]
) -> dict[str, Any]:
    existing = repository.find_by_key(session, key)
    if existing is not None:
        raise DuplicateKey(_response(session, existing))
    tipo = fields.get("tipo", "")
    if tipo not in TIPOS:
        raise _invalid(f"tipo must be one of {sorted(TIPOS)}")
    if "ocurrido_en" not in fields:
        raise _invalid("ocurrido_en is required")
    zone_id = fields.get("zone_id", "")
    if not zones.zone_exists(session, zone_id):
        raise ApiError(404, "zone_not_found", f"zone_id {zone_id} does not exist")
    report = Report(
        idempotency_key=key,
        tipo=tipo,
        zone_id=zone_id,
        lat=_number(fields, "lat"),
        lon=_number(fields, "lon"),
        ocurrido_en=_moment(fields["ocurrido_en"]),
        foto=_attachment(files, "foto", MAX_FOTO_BYTES),
        audio=_attachment(files, "audio", MAX_AUDIO_BYTES),
    )
    return _response(session, repository.add(session, report))


def _cell_polygon(lat: float, lon: float) -> dict[str, Any]:
    h = CELL_DEG / 2
    ring = [[lon - h, lat - h], [lon + h, lat - h], [lon + h, lat + h], [lon - h, lat + h]]
    return {"type": "Polygon", "coordinates": [[*ring, ring[0]]]}


def _direction(origin_lat: float, origin_lon: float, lat: float, lon: float) -> str | None:
    dx = (lon - origin_lon) * math.cos(math.radians(origin_lat))
    dy = lat - origin_lat
    if math.hypot(dx, dy) < CELL_DEG / 2:
        return None
    sector = round(math.degrees(math.atan2(dy, dx)) / 45) % 8
    return DIRECTIONS[sector]


def zone_map(session: Session, zone_id: str) -> dict[str, Any]:
    zone = zones.get_zone(session, zone_id)
    cells: dict[tuple[float, float], int] = {}
    for r in repository.recent(session, zone_id, "sin_agua", datetime.now(UTC) - WEEK):
        if r.lat is None or r.lon is None:
            continue
        key = (round(r.lat / CELL_DEG) * CELL_DEG, round(r.lon / CELL_DEG) * CELL_DEG)
        cells[key] = cells.get(key, 0) + 1
    shown = sorted(
        (
            (round(lat, 2), round(lon, 2), n)
            for (lat, lon), n in cells.items()
            if n >= MIN_REPORTS_PER_CELL
        ),
        key=lambda c: -c[2],
    )
    resumen: dict[str, Any] = {"sin_agua_vecinos": sum(n for _, _, n in shown), "periodo_dias": 7}
    if shown:
        direction = _direction(zone.lat, zone.lon, shown[0][0], shown[0][1])
        if direction:
            resumen["direccion"] = direction
    inundable = []
    if zone.cerca_drenaje is not None:
        inundable.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [zone.lon, zone.lat]},
                "properties": {"cerca_drenaje_m": zone.cerca_drenaje, "fuente": "gamc_wms"},
            }
        )
    return {
        "actualizado_en": datetime.now(LA_PAZ).isoformat(timespec="seconds"),
        "resumen": resumen,
        "capas": {
            "sin_agua": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": _cell_polygon(lat, lon),
                        "properties": {"reportes": n},
                    }
                    for lat, lon, n in shown
                ],
            },
            "inundable": {"type": "FeatureCollection", "features": inundable},
        },
        "historial": alerts.zone_history(session, zone_id),
    }
