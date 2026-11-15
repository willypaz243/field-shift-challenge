from datetime import date

from sqlmodel import Session

from api.modules.climate.models import Forecast
from api.tests.contract import contract_errors


def add_days(engine):
    with Session(engine) as session:
        for d, tmin in ((date(2026, 12, 31), 9.4), (date(2027, 1, 1), -0.5)):
            session.add(
                Forecast(
                    zone_id="D9_itocta",
                    fecha=d,
                    anio=d.year,
                    tmin=tmin,
                    tmax=23.8,
                    tmean=15.9,
                    pmm=4.4,
                    et0=4.7,
                    tmin_min=tmin - 1.5,
                    tmin_max=tmin + 4,
                    pmm_min=0.0,
                    pmm_max=15.7,
                )
            )
        session.commit()


def test_forecast_returns_days_with_uncertainty_band(client, engine):
    add_days(engine)

    body = client.get("/zones/D9_itocta/forecast").json()

    assert [d["fecha"] for d in body["dias"]] == ["2026-12-31", "2027-01-01"]
    assert body["dias"][1]["incert_min"] == {"tmin": -2.0, "pmm": 0.0}
    assert body["dias"][1]["incert_max"] == {"tmin": 3.5, "pmm": 15.7}
    assert body["dias"][1]["et0"] == 4.7


def test_forecast_includes_model_info_and_et0(client, engine):
    add_days(engine)

    body = client.get("/zones/D9_itocta/forecast").json()

    assert body["modelo"]["tipo"] == "fourier_tendencia"
    assert body["modelo"]["backtest"]["mae"]["tmin"] is not None
    assert body["dias"][0]["et0"] == 4.7
    assert "rh" not in body["dias"][0]


def test_forecast_filters_by_year(client, engine):
    add_days(engine)

    body = client.get("/zones/D9_itocta/forecast", params={"anio": 2027}).json()

    assert (body["anio"], [d["fecha"] for d in body["dias"]]) == (2027, ["2027-01-01"])


def test_forecast_unknown_zone_returns_404(client):
    response = client.get("/zones/D99_x/forecast")

    assert (response.status_code, response.json()["error"]["codigo"]) == (404, "zone_not_found")


def test_forecast_follows_the_contract(client, engine):
    add_days(engine)

    assert contract_errors("Forecast", client.get("/zones/D9_itocta/forecast").json()) == []
