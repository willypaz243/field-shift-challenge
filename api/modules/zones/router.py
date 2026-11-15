from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api.core.db import get_session
from api.modules.zones import service
from api.modules.zones.schemas import ZonesResponse

router = APIRouter(tags=["zones"])


@router.get("/zones", response_model=ZonesResponse)
def list_zones(session: Annotated[Session, Depends(get_session)]) -> ZonesResponse:
    return service.list_zones(session)
