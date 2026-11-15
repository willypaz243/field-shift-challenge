from sqlmodel import Session

from api.modules.feedback import repository
from api.modules.feedback.models import Feedback
from api.modules.feedback.schemas import FeedbackIn


def create_feedback(session: Session, data: FeedbackIn) -> Feedback:
    return repository.add_feedback(session, Feedback(**data.model_dump()))
