import json
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session

from api.core.models import SyncVersion
from api.modules.zones.models import Zone

ROOT = Path(__file__).resolve().parents[2]


def add_itocta_details(engine):
    with Session(engine) as session:
        zone = session.get(Zone, "D9_itocta")
        zone.nombre, zone.comuna, zone.distrito = "Itocta", "ITOCTA", "D9"
        zone.elev_m, zone.pendiente, zone.cerca_drenaje = 2590.0, 2.1, 1
        session.add(zone)
        session.add(SyncVersion(creado_en=datetime(2026, 11, 14, 10, tzinfo=UTC), hash=""))
        session.commit()


def test_get_zones_returns_zones_from_the_database(client, engine):
    add_itocta_details(engine)

    body = client.get("/zones").json()

    assert body["zones"] == [
        {
            "id": "D9_itocta",
            "nombre": "Itocta",
            "comuna": "ITOCTA",
            "distrito": 9,
            "lat": -17.4611,
            "lon": -66.2185,
            "elev_m": 2590.0,
            "pendiente": 2.1,
            "es_agricola": True,
            "cerca_drenaje": 1,
            "altitud_alta": False,
        }
    ]
    assert body["actualizado_en"].startswith("2026-11-14T10:00:00")
    assert body["fuente"] == ["gamc_wms", "srtm"]


def test_get_crops_returns_the_catalog_file(client):
    catalog = json.loads((ROOT / "data" / "crops" / "crops.json").read_text())

    body = client.get("/crops").json()

    assert body == catalog
    assert body["version"] == catalog["version"]


def test_responses_have_etag_and_304_when_unchanged(client):
    first = client.get("/crops")
    again = client.get("/crops", headers={"If-None-Match": first.headers["ETag"]})

    assert first.headers["ETag"]
    assert again.status_code == 304
    assert again.content == b""


def test_large_responses_are_gzipped(client):
    response = client.get("/crops", headers={"Accept-Encoding": "gzip"})

    assert response.headers["Content-Encoding"] == "gzip"


def test_zones_and_crops_follow_the_openapi_contract(client, engine):
    import yaml
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012

    add_itocta_details(engine)
    spec = yaml.safe_load((ROOT / "api" / "openapi.yaml").read_text())
    registry = Registry().with_resource(
        "urn:spec", Resource.from_contents(spec, default_specification=DRAFT202012)
    )

    for path, schema in (("/zones", "ZonesResponse"), ("/crops", "CropsCatalog")):
        validator = Draft202012Validator(
            {"$ref": f"urn:spec#/components/schemas/{schema}"}, registry=registry
        )
        assert not list(validator.iter_errors(client.get(path).json())), path
