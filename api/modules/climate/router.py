from datetime import date
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


@router.get("/zones/{zone_id}/climatology")
def get_climatology(
    zone_id: str, session: Annotated[Session, Depends(get_session)]
) -> dict[str, Any]:
    return service.zone_climatology(session, zone_id)


@router.get("/zones/{zone_id}/history")
def get_history(
    zone_id: str,
    session: Annotated[Session, Depends(get_session)],
    desde: Annotated[date | None, Query()] = None,
    hasta: Annotated[date | None, Query()] = None,
) -> dict[str, Any]:
    return service.zone_history(session, zone_id, desde, hasta)
