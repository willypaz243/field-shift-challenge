from sqlmodel import Session

from api.modules.crops.models import Crop


def get_crop(session: Session, crop_id: str) -> Crop | None:
    return session.get(Crop, crop_id)
