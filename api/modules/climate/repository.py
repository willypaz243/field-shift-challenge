from sqlmodel import Session, select

from api.modules.climate.models import Forecast


def forecast_days(session: Session, zone_id: str, anio: int | None = None) -> list[Forecast]:
    query = select(Forecast).where(Forecast.zone_id == zone_id)
    if anio is not None:
        query = query.where(Forecast.anio == anio)
    return list(session.exec(query.order_by(Forecast.fecha)))
