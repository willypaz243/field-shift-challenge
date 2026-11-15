from sqlmodel import Session, select

from api.modules.climate.models import Forecast


def forecast_days(session: Session, zone_id: str) -> list[Forecast]:
    return list(
        session.exec(select(Forecast).where(Forecast.zone_id == zone_id).order_by(Forecast.fecha))
    )
