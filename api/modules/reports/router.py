from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session

from api.core.db import get_session
from api.core.multipart import parse_form
from api.modules.reports import service

router = APIRouter(tags=["reports"])

SessionDep = Annotated[Session, Depends(get_session)]


async def report_form(request: Request) -> tuple[dict[str, str], dict[str, tuple[str, bytes]]]:
    return parse_form(request.headers.get("content-type", ""), await request.body())


@router.post("/reports", status_code=201)
def create_report(
    session: SessionDep,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    form: Annotated[tuple[dict[str, str], dict[str, tuple[str, bytes]]], Depends(report_form)],
) -> Any:
    try:
        return service.create_report(session, idempotency_key, *form)
    except service.DuplicateKey as dup:
        return JSONResponse(status_code=409, content=dup.response)


@router.get("/zones/{zone_id}/map")
def get_map(zone_id: str, session: SessionDep) -> dict[str, Any]:
    return service.zone_map(session, zone_id)
