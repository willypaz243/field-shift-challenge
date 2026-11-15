from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from api.core.db import get_session
from api.modules.climate import service

router = APIRouter(tags=["climate"])


@router.get("/zones/{zone_id}/forecast")
def get_forecast(
    zone_id: str,
    session: Annotated[Session, Depends(get_session)],
    anio: Annotated[int | None, Query()] = None,
) -> dict[str, Any]:
    return service.zone_forecast(session, zone_id, anio)
