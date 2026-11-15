from datetime import date

from sqlmodel import Session

from api.modules.water.models import Reservoir
from api.tests.contract import contract_errors


def add_angostura(engine, nivel_pct=34.0):
    with Session(engine) as session:
        session.add(
            Reservoir(
                id="angostura",
                nombre="La Angostura",
                nivel_pct=nivel_pct,
                volumen_hm3=25.5,
                actualizado_en=date(2026, 11, 15),
            )
        )
        session.commit()


def test_reservoir_returns_level_state_and_source(client, engine):
    add_angostura(engine)

    body = client.get("/reservoirs/la-angostura").json()

    assert (body["nivel_pct"], body["volumen_hm3"], body["estado"]) == (34.0, 25.5, "bajo")
    assert body["fuente"] == ["riego_n1"]
    assert body["actualizado_en"].startswith("2026-11-15")


def test_reservoir_without_data_returns_404(client):
    response = client.get("/reservoirs/la-angostura")

    assert (response.status_code, response.json()["error"]["codigo"]) == (
        404,
        "reservoir_not_found",
    )


def test_reservoir_follows_the_contract(client, engine):
    add_angostura(engine, nivel_pct=15.0)

    body = client.get("/reservoirs/la-angostura").json()

    assert body["estado"] == "critico"
    assert contract_errors("Reservoir", body) == []
