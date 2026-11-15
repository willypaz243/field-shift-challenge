from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api.core.db import get_session
from api.core.errors import ApiError
from api.modules.water import service

router = APIRouter(tags=["water"])


@router.get("/reservoirs/la-angostura")
def get_la_angostura(session: Annotated[Session, Depends(get_session)]) -> dict[str, Any]:
    reservoir = service.la_angostura(session)
    if reservoir is None:
        raise ApiError(404, "reservoir_not_found", "no data for La Angostura yet")
    return reservoir
