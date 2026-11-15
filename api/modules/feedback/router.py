from typing import Annotated

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlmodel import Session

from api.core.db import get_session
from api.modules.feedback import service
from api.modules.feedback.schemas import Created, FeedbackIn, PlanIn

router = APIRouter(tags=["feedback"])

SessionDep = Annotated[Session, Depends(get_session)]
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key")]


@router.post("/feedback", status_code=201, response_model=Created)
def create_feedback(data: FeedbackIn, session: SessionDep, idempotency_key: IdempotencyKey):
    try:
        feedback = service.create_feedback(session, data, idempotency_key)
    except service.DuplicateKey as dup:
        return JSONResponse(status_code=409, content={"id": str(dup.existing_id)})
    return Created(id=str(feedback.id))


@router.post("/plans", status_code=201, response_model=Created)
def create_plan(data: PlanIn, session: SessionDep, idempotency_key: IdempotencyKey):
    try:
        plan = service.create_plan(session, data, idempotency_key)
    except service.DuplicateKey as dup:
        return JSONResponse(status_code=409, content={"id": str(dup.existing_id)})
    return Created(id=str(plan.id))
