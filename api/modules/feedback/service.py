from sqlmodel import Session

from api.core.errors import ApiError
from api.modules.crops.service import crop_exists
from api.modules.feedback import repository
from api.modules.feedback.models import Feedback, Plan
from api.modules.feedback.schemas import FeedbackIn, PlanIn
from api.modules.zones.service import zone_exists


class DuplicateKey(Exception):
    def __init__(self, existing_id: int) -> None:
        super().__init__(existing_id)
        self.existing_id = existing_id


def _require_zone(session: Session, zone_id: str) -> None:
    if not zone_exists(session, zone_id):
        raise ApiError(404, "zone_not_found", f"zone_id {zone_id} does not exist")


def _reject_duplicate(session: Session, model: type[Feedback] | type[Plan], key: str) -> None:
    existing = repository.find_by_key(session, model, key)
    if existing is not None:
        raise DuplicateKey(existing.id)


def create_feedback(session: Session, data: FeedbackIn, idempotency_key: str) -> Feedback:
    _reject_duplicate(session, Feedback, idempotency_key)
    _require_zone(session, data.zone_id)
    if not crop_exists(session, data.crop_id):
        raise ApiError(404, "crop_not_found", f"crop_id {data.crop_id} does not exist")
    return repository.add(session, Feedback(idempotency_key=idempotency_key, **data.model_dump()))


def create_plan(session: Session, data: PlanIn, idempotency_key: str) -> Plan:
    _reject_duplicate(session, Plan, idempotency_key)
    _require_zone(session, data.zone_id)
    return repository.add(session, Plan(idempotency_key=idempotency_key, **data.model_dump()))


def results_by_zone(session: Session, zone_id: str) -> list[Feedback]:
    return repository.list_feedback_by_zone(session, zone_id)
