from datetime import date

from sqlalchemy import func
from sqlmodel import Session, select

from api.modules.climate.models import ClimateHistory, Forecast, WeatherDay


def forecast_days(session: Session, zone_id: str, anio: int | None = None) -> list[Forecast]:
    query = select(Forecast).where(Forecast.zone_id == zone_id)
    if anio is not None:
        query = query.where(Forecast.anio == anio)
    return list(session.exec(query.order_by(Forecast.fecha)))


def history_rows(
    session: Session, zone_id: str, desde: date | None = None, hasta: date | None = None
) -> list[ClimateHistory]:
    query = select(ClimateHistory).where(ClimateHistory.zone_id == zone_id)
    if desde is not None:
        query = query.where(ClimateHistory.fecha >= desde)
    if hasta is not None:
        query = query.where(ClimateHistory.fecha <= hasta)
    return list(session.exec(query.order_by(ClimateHistory.fecha)))


def last_history_date(session: Session, zone_id: str) -> date | None:
    return session.exec(
        select(func.max(ClimateHistory.fecha)).where(ClimateHistory.zone_id == zone_id)
    ).first()


def weather_days(session: Session, zone_id: str, desde: date, limit: int) -> list[WeatherDay]:
    return list(
        session.exec(
            select(WeatherDay)
            .where(WeatherDay.zone_id == zone_id, WeatherDay.fecha >= desde)
            .order_by(WeatherDay.fecha)
            .limit(limit)
        )
    )
