import json

from sqlmodel import Session

from api.core.config import data_dir
from api.modules.crops.models import Crop


def get_crop(session: Session, crop_id: str) -> Crop | None:
    return session.get(Crop, crop_id)


def read_catalog() -> dict:
    return json.loads((data_dir() / "crops" / "crops.json").read_text())
