from sqlmodel import Session

from api.modules.zones.models import Zone


def get_zone(session: Session, zone_id: str) -> Zone | None:
    return session.get(Zone, zone_id)
