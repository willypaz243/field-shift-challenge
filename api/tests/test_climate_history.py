from datetime import date

from sqlmodel import Session

from api.modules.climate.models import ClimateHistory
from api.tests.contract import contract_errors


def add_history(engine, rows):
    with Session(engine) as session:
        for fecha, tmin, tmax, pmm_sat in rows:
            session.add(
                ClimateHistory(
                    zone_id="D9_itocta", fecha=fecha, tmin=tmin, tmax=tmax, pmm=1.0, pmm_sat=pmm_sat
                )
            )
        session.commit()


JULY = [
    (date(2016, 7, 1), -1.0, 20.0, 0.0),
    (date(2016, 7, 2), 3.0, 22.0, 2.0),
    (date(2017, 7, 1), 2.0, 24.0, 6.0),
]


def test_climatology_averages_each_month_over_the_years(client, engine):
    add_history(engine, JULY)

    body = client.get("/zones/D9_itocta/climatology").json()

    july = next(m for m in body["meses"] if m["mes"] == 7)
    assert july == {"mes": 7, "pmm_total": 4.0, "tmin": 1.3, "tmax": 22.0, "p_helada": 0.5}
    assert body["periodo"] == {"power": "2016-2017", "imerg": "2016-2017"}


def test_climatology_leaves_out_months_without_data(client, engine):
    add_history(engine, JULY)

    body = client.get("/zones/D9_itocta/climatology").json()

    assert [m["mes"] for m in body["meses"]] == [7]


def test_history_marks_the_imerg_utc_day(client, engine):
    add_history(
        engine, [(date(2025, 12, 30), 6.1, 27.4, 3.2), (date(2025, 12, 31), 6.0, 27.0, None)]
    )

    body = client.get(
        "/zones/D9_itocta/history", params={"desde": "2025-12-30", "hasta": "2025-12-31"}
    ).json()

    assert body["dias"] == [
        {
            "fecha": "2025-12-30",
            "tmin": 6.1,
            "tmax": 27.4,
            "fecha_utc": "2025-12-30",
            "pmm": 3.2,
            "pmm_producto": "late",
            "pmm_revision": "V07",
        },
        {"fecha": "2025-12-31", "tmin": 6.0, "tmax": 27.0},
    ]


def test_history_defaults_to_the_last_four_weeks_with_data(client, engine):
    add_history(engine, [(date(2025, 11, 1), 5.0, 25.0, 0.0), (date(2025, 12, 31), 6.0, 27.0, 0.0)])

    body = client.get("/zones/D9_itocta/history").json()

    assert [d["fecha"] for d in body["dias"]] == ["2025-12-31"]


def test_history_rejects_a_range_longer_than_a_year(client):
    response = client.get(
        "/zones/D9_itocta/history", params={"desde": "2020-01-01", "hasta": "2025-01-01"}
    )

    assert (response.status_code, response.json()["error"]["codigo"]) == (400, "invalid_request")


def test_unknown_zone_returns_404(client):
    for path in ("/zones/D99_x/climatology", "/zones/D99_x/history"):
        response = client.get(path)
        assert (response.status_code, response.json()["error"]["codigo"]) == (404, "zone_not_found")


def test_climatology_and_history_follow_the_contract(client, engine):
    add_history(engine, JULY)

    assert contract_errors("Climatology", client.get("/zones/D9_itocta/climatology").json()) == []
    history = client.get(
        "/zones/D9_itocta/history", params={"desde": "2016-07-01", "hasta": "2016-07-02"}
    )
    assert contract_errors("History", history.json()) == []
