from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api.core.db import get_session
from api.modules.alerts import service

router = APIRouter(tags=["alerts"])


@router.get("/zones/{zone_id}/alerts")
def get_alerts(zone_id: str, session: Annotated[Session, Depends(get_session)]) -> dict[str, Any]:
    return service.zone_alerts(session, zone_id)
