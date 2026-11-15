from sqlmodel import Session

from api.modules.water.models import Reservoir


def get_reservoir(session: Session, reservoir_id: str) -> Reservoir | None:
    return session.get(Reservoir, reservoir_id)
