from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlmodel import Session

from api.modules.climate.models import WeatherDay
from api.tests.contract import contract_errors

LA_PAZ = ZoneInfo("America/La_Paz")


def today() -> date:
    return datetime.now(LA_PAZ).date()


def add_weather(engine, first: date, count: int, updated: datetime):
    with Session(engine) as session:
        for i in range(count):
            session.add(
                WeatherDay(
                    zone_id="D9_itocta",
                    fecha=first + timedelta(days=i),
                    tmin=-2.0 + i,
                    tmax=24.0,
                    pmm=0.0,
                    granizo=i == 1,
                    confianza="alta" if i < 7 else "media",
                    fuente="nasa_geos",
                    actualizado_en=updated,
                )
            )
        session.commit()


def test_weather_returns_fourteen_days_from_today_in_bolivia(client, engine):
    add_weather(engine, today() - timedelta(days=2), 20, datetime.now(UTC))

    body = client.get("/zones/D9_itocta/weather").json()

    assert len(body["dias"]) == 14
    assert body["dias"][0]["fecha"] == today().isoformat()
    assert body["dias"][0]["granizo"] is False
    assert (body["fuente"], body["desactualizado"]) == (["nasa_geos"], False)


def test_weather_limits_the_number_of_days(client, engine):
    add_weather(engine, today(), 14, datetime.now(UTC))

    body = client.get("/zones/D9_itocta/weather", params={"dias": 3}).json()

    assert [d["fecha"] for d in body["dias"]] == [
        (today() + timedelta(days=i)).isoformat() for i in range(3)
    ]


def test_old_data_is_returned_marked_out_of_date(client, engine):
    add_weather(engine, today() - timedelta(days=3), 14, datetime.now(UTC) - timedelta(days=3))

    body = client.get("/zones/D9_itocta/weather").json()

    assert (len(body["dias"]), body["desactualizado"]) == (11, True)


def test_weather_without_data_is_empty_and_out_of_date(client):
    body = client.get("/zones/D9_itocta/weather").json()

    assert (body["dias"], body["desactualizado"]) == ([], True)


def test_weather_rejects_more_than_fourteen_days(client):
    response = client.get("/zones/D9_itocta/weather", params={"dias": 15})

    assert (response.status_code, response.json()["error"]["codigo"]) == (400, "invalid_request")


def test_weather_unknown_zone_returns_404(client):
    response = client.get("/zones/D99_x/weather")

    assert (response.status_code, response.json()["error"]["codigo"]) == (404, "zone_not_found")


def test_weather_follows_the_contract(client, engine):
    add_weather(engine, today(), 14, datetime.now(UTC))

    assert contract_errors("Weather", client.get("/zones/D9_itocta/weather").json()) == []
