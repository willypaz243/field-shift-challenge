from sqlmodel import Session, col, or_, select

from api.modules.alerts.models import Event


def events_for_zone(session: Session, zone_id: str) -> list[Event]:
    query = select(Event).where(or_(Event.zone_id == zone_id, col(Event.zone_id).is_(None)))
    return list(session.exec(query.order_by(col(Event.fecha).desc(), Event.id)))
