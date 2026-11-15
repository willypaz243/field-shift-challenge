from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from api.core.db import get_session
from api.modules.climate import service
from api.modules.climate.schemas import ForecastResponse

router = APIRouter(tags=["climate"])


@router.get(
    "/zones/{zone_id}/forecast",
    response_model=ForecastResponse,
    response_model_exclude_none=True,
)
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


@router.get("/zones/{zone_id}/weather")
def get_weather(
    zone_id: str,
    session: Annotated[Session, Depends(get_session)],
    dias: Annotated[int, Query()] = service.WEATHER_MAX_DAYS,
) -> dict[str, Any]:
    return service.zone_weather(session, zone_id, dias)
