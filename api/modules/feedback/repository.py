from sqlmodel import Session

from api.modules.feedback.models import Feedback


def add_feedback(session: Session, feedback: Feedback) -> Feedback:
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback
