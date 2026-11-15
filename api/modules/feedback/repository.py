from sqlmodel import Session, select

from api.modules.feedback.models import Feedback, Plan


def add[T: Feedback | Plan](session: Session, row: T) -> T:
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def find_by_key(
    session: Session, model: type[Feedback] | type[Plan], key: str
) -> Feedback | Plan | None:
    return session.exec(select(model).where(model.idempotency_key == key)).first()


def list_feedback_by_zone(session: Session, zone_id: str) -> list[Feedback]:
    return list(session.exec(select(Feedback).where(Feedback.zone_id == zone_id)))
