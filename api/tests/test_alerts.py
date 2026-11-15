from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlmodel import Session

from api.modules.climate.models import WeatherDay
from api.modules.water.models import Reservoir
from api.tests.contract import contract_errors

LA_PAZ = ZoneInfo("America/La_Paz")


def today() -> date:
    return datetime.now(LA_PAZ).date()


def add_weather(engine, days):
    with Session(engine) as session:
        for offset, tmin, granizo, confianza in days:
            session.add(
                WeatherDay(
                    zone_id="D9_itocta",
                    fecha=today() + timedelta(days=offset),
                    tmin=tmin,
                    tmax=24.0,
                    pmm=0.0,
                    granizo=granizo,
                    confianza=confianza,
                    fuente="nasa_geos",
                    actualizado_en=datetime.now(UTC),
                )
            )
        session.commit()


def add_reservoir(engine, nivel_pct, updated):
    with Session(engine) as session:
        session.add(
            Reservoir(
                id="angostura", nombre="La Angostura", nivel_pct=nivel_pct, actualizado_en=updated
            )
        )
        session.commit()


def alerts(client):
    return client.get("/zones/D9_itocta/alerts").json()["alertas"]


def test_frost_in_the_short_forecast_raises_a_frost_alert(client, engine):
    add_weather(engine, [(1, 3.0, False, "alta"), (5, -2.0, False, "alta")])

    frost = alerts(client)

    day = today() + timedelta(days=5)
    assert frost == [
        {
            "id": f"helada-{day.isoformat()}",
            "tipo": "helada",
            "fecha_evento": day.isoformat(),
            "momento": "madrugada",
            "valor": {"tmin": -2.0},
            "confianza": "alta",
            "volver_a_avisar": (day - timedelta(days=1)).isoformat(),
            "regla": {"id": "helada-tmin-0"},
        }
    ]


def test_hail_in_the_short_forecast_raises_a_hail_alert(client, engine):
    add_weather(engine, [(2, 8.0, True, "media")])

    assert [(a["tipo"], a["confianza"]) for a in alerts(client)] == [("granizo", "media")]


def test_low_reservoir_raises_an_alert(client, engine):
    add_reservoir(engine, 34.0, today() - timedelta(days=3))

    assert alerts(client) == [
        {"id": "represa_baja", "tipo": "represa_baja", "valor": {"nivel_pct": 34.0}}
    ]


def test_an_old_reservoir_reading_does_not_raise_an_alert(client, engine):
    add_reservoir(engine, 5.0, date(2002, 11, 27))

    assert alerts(client) == []


def test_a_normal_reservoir_does_not_raise_an_alert(client, engine):
    add_reservoir(engine, 60.0, today())

    assert alerts(client) == []


def test_alerts_are_sorted_by_event_date(client, engine):
    add_weather(engine, [(4, -1.0, True, "media"), (2, -3.0, False, "alta")])

    assert [a["fecha_evento"] for a in alerts(client)] == sorted(
        a["fecha_evento"] for a in alerts(client)
    )


def test_alerts_unknown_zone_returns_404(client):
    response = client.get("/zones/D99_x/alerts")

    assert (response.status_code, response.json()["error"]["codigo"]) == (404, "zone_not_found")


def test_alerts_follow_the_contract(client, engine):
    add_weather(engine, [(1, -2.0, True, "alta")])
    add_reservoir(engine, 15.0, today())

    assert contract_errors("Alerts", client.get("/zones/D9_itocta/alerts").json()) == []
