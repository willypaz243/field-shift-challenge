from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlmodel import Session

from api.core.db import get_session
from api.modules.feedback import service
from api.modules.feedback.schemas import Created, FeedbackIn

router = APIRouter(tags=["feedback"])

SessionDep = Annotated[Session, Depends(get_session)]
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key")]


@router.post("/feedback", status_code=201, response_model=Created)
def create_feedback(
    data: FeedbackIn, session: SessionDep, idempotency_key: IdempotencyKey
) -> Created:
    feedback = service.create_feedback(session, data)
    return Created(id=str(feedback.id))
