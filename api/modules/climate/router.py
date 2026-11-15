from typing import Annotated, Any

from fastapi import APIRouter, Depends
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
def get_forecast(zone_id: str, session: Annotated[Session, Depends(get_session)]) -> dict[str, Any]:
    return service.forecast(session, zone_id)
