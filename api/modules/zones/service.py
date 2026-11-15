from sqlmodel import Session

from api.modules.zones import repository


def zone_exists(session: Session, zone_id: str) -> bool:
    return repository.get_zone(session, zone_id) is not None
