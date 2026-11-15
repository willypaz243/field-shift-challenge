from typing import Any

from sqlmodel import Session

from api.modules.alerts import repository


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


def active_alerts(session: Session, zone_id: str) -> list[dict[str, Any]]:
    return []
