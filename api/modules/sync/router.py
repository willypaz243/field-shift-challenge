from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlmodel import Session

from api.core.db import get_session
from api.modules.sync import service

router = APIRouter(tags=["sync"])


@router.get("/sync")
def get_sync(
    session: Annotated[Session, Depends(get_session)],
    zone_id: Annotated[str, Query()],
    desde_version: Annotated[int | None, Query()] = None,
):
    if desde_version is not None and desde_version >= service.current_version(session):
        service.ensure_zone(session, zone_id)
        return Response(status_code=304)
    return service.package(session, zone_id)
