import gzip
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlmodel import Session

from api.core.models import SyncVersion
from api.modules.alerts.models import Event
from api.modules.climate.models import Forecast
from api.modules.water.models import Reservoir

ROOT = Path(__file__).resolve().parents[2]
SECTIONS = {
    "zone",
    "crops",
    "forecast",
    "corto_plazo",
    "climatologia",
    "alertas",
    "rotaciones",
    "represa",
    "historial_zona",
}


def seed(engine, versions=1):
    with Session(engine) as session:
        for v in range(versions):
            session.add(SyncVersion(creado_en=datetime(2026, 11, 14, 10 + v, tzinfo=UTC), hash=""))
        session.add(
            Reservoir(
                id="angostura",
                nombre="La Angostura",
                nivel_pct=34.0,
                volumen_hm3=25.5,
                actualizado_en=date(2026, 11, 15),
            )
        )
        session.add(
            Event(
                tipo="inundacion",
                fecha=date(2024, 3, 10),
                zone_id="D9_itocta",
                descripcion="canal Valverde",
                fuente="prensa",
            )
        )
        session.add(
            Event(tipo="helada", fecha=date(2024, 7, 4), zone_id="D3_molle", fuente="prensa")
        )
        session.commit()


def test_sync_returns_all_sections_with_data_from_the_database(client, engine):
    seed(engine)

    body = client.get("/sync", params={"zone_id": "D9_itocta"}).json()

    assert body["sync_version"] == 1 and body["hash"]
    assert SECTIONS <= set(body)
    assert body["zone"]["id"] == "D9_itocta"
    assert [c["id"] for c in body["crops"]["crops"]][:1] == ["papa"]
    assert (body["represa"]["nivel_pct"], body["represa"]["estado"]) == (34.0, "bajo")
    assert [(e["fecha"], e["tipo"]) for e in body["historial_zona"]] == [
        ("2024-03-10", "inundacion")
    ]


def test_sync_unknown_zone_returns_404(client, engine):
    seed(engine)

    response = client.get("/sync", params={"zone_id": "D99_x"})

    assert (response.status_code, response.json()["error"]["codigo"]) == (404, "zone_not_found")


def test_sync_same_version_returns_304(client, engine):
    seed(engine, versions=2)

    response = client.get("/sync", params={"zone_id": "D9_itocta", "desde_version": 2})

    assert response.status_code == 304
    assert response.content == b""


def test_sync_older_version_returns_the_full_package(client, engine):
    seed(engine, versions=2)

    response = client.get("/sync", params={"zone_id": "D9_itocta", "desde_version": 1})

    assert response.status_code == 200
    assert response.json()["sync_version"] == 2
    assert SECTIONS <= set(response.json())


def test_sync_hash_changes_only_when_data_changes(client, engine):
    seed(engine)
    first = client.get("/sync", params={"zone_id": "D9_itocta"}).json()["hash"]
    same = client.get("/sync", params={"zone_id": "D9_itocta"}).json()["hash"]

    with Session(engine) as session:
        session.add(
            Event(tipo="granizo", fecha=date(2025, 11, 17), zone_id="D9_itocta", fuente="prensa")
        )
        session.commit()
    changed = client.get("/sync", params={"zone_id": "D9_itocta"}).json()["hash"]

    assert first == same
    assert changed != first


def test_sync_follows_the_openapi_contract(client, engine):
    import yaml
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012

    seed(engine)
    spec = yaml.safe_load((ROOT / "api" / "openapi.yaml").read_text())
    registry = Registry().with_resource(
        "urn:spec", Resource.from_contents(spec, default_specification=DRAFT202012)
    )
    validator = Draft202012Validator(
        {"$ref": "urn:spec#/components/schemas/Sync"}, registry=registry
    )

    body = client.get("/sync", params={"zone_id": "D9_itocta"}).json()

    assert not list(validator.iter_errors(body))


def test_sync_with_a_full_year_forecast_is_under_500_kb_gzipped(client, engine):
    seed(engine)
    with Session(engine) as session:
        start = date(2027, 1, 1)
        for i in range(365):
            session.add(
                Forecast(
                    zone_id="D9_itocta",
                    fecha=start + timedelta(days=i),
                    anio=2027,
                    tmin=5.0,
                    tmax=24.0,
                    tmean=14.5,
                    pmm=2.5,
                    et0=4.1,
                    rh=60.0,
                    sw=21.0,
                    ws=2.0,
                    sm_surface=0.25,
                    sm_root=0.3,
                    tmin_min=3.0,
                    tmin_max=7.0,
                    pmm_min=0.0,
                    pmm_max=8.0,
                )
            )
        session.commit()

    response = client.get("/sync", params={"zone_id": "D9_itocta"})

    assert len(response.json()["forecast"]["dias"]) == 365
    assert len(gzip.compress(response.content)) <= 500_000
