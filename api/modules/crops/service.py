from sqlmodel import Session

from api.modules.crops import repository


def crop_exists(session: Session, crop_id: str) -> bool:
    return repository.get_crop(session, crop_id) is not None
