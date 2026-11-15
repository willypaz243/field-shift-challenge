from sqlmodel import Session, select

from api.core.models import SyncVersion
from api.modules.zones.models import Zone


def get_zone(session: Session, zone_id: str) -> Zone | None:
    return session.get(Zone, zone_id)


def list_zones(session: Session) -> list[Zone]:
    return list(session.exec(select(Zone).order_by(Zone.id)))


def last_load(session: Session) -> SyncVersion | None:
    return session.exec(select(SyncVersion).order_by(SyncVersion.creado_en.desc())).first()
