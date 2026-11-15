from fastapi import APIRouter

from api.modules.crops import service

router = APIRouter(tags=["crops"])


@router.get("/crops")
def get_catalog() -> dict:
    return service.catalog()
