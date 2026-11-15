from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from api.modules.alerts.models import Event
from api.modules.reports.models import Report
from api.modules.zones.models import Zone
from api.tests.contract import contract_errors


def form(**overrides):
    data = {
        "tipo": "sin_agua",
        "zone_id": "D9_itocta",
        "lat": "-17.46123",
        "lon": "-66.21849",
        "ocurrido_en": datetime.now(UTC).isoformat(),
    }
    return {**data, **overrides}


def post(client, key="key-1", files=None, **overrides):
    return client.post(
        "/reports", data=form(**overrides), files=files, headers={"Idempotency-Key": key}
    )


def test_report_is_stored_with_location_rounded_to_three_decimals(client, engine):
    response = post(client, files={"foto": ("f.jpg", b"\xff\xd8jpeg", "image/jpeg")})

    assert response.status_code == 201
    assert response.json()["id"].startswith("rep-")
    with Session(engine) as session:
        report = session.exec(select(Report)).one()
    assert (report.lat, report.lon, report.foto) == (-17.461, -66.218, b"\xff\xd8jpeg")


def test_repeated_key_returns_409_with_the_original_report(client):
    first = post(client).json()

    again = post(client, tipo="helada")

    assert (again.status_code, again.json()) == (409, first)


def test_response_counts_neighbours_with_the_same_type_this_week(client):
    post(client, key="a")
    post(client, key="b", ocurrido_en=(datetime.now(UTC) - timedelta(days=10)).isoformat())
    post(client, key="c", tipo="helada")

    body = post(client, key="d").json()

    assert body["vecinos_mismo_tipo_semana"] == 1


def test_report_with_unknown_type_is_rejected(client):
    response = post(client, tipo="lluvia")

    assert (response.status_code, response.json()["error"]["codigo"]) == (400, "invalid_request")


def test_report_without_key_is_rejected(client):
    response = client.post("/reports", data=form())

    assert response.status_code == 400


def test_report_with_a_big_photo_is_rejected(client):
    big = b"\xff\xd8" + b"0" * 300_001
    response = post(client, files={"foto": ("f.jpg", big, "image/jpeg")})

    assert (response.status_code, response.json()["error"]["codigo"]) == (400, "invalid_request")


def test_report_for_unknown_zone_returns_404(client):
    response = post(client, zone_id="D99_x")

    assert (response.status_code, response.json()["error"]["codigo"]) == (404, "zone_not_found")


def test_map_shows_only_cells_with_three_reports_this_week(client):
    for i in range(3):
        post(client, key=f"near-{i}", lat=f"-17.46{i}", lon="-66.205")
    post(client, key="alone", lat="-17.400", lon="-66.100")
    post(client, key="old", ocurrido_en=(datetime.now(UTC) - timedelta(days=9)).isoformat())

    body = client.get("/zones/D9_itocta/map").json()

    features = body["capas"]["sin_agua"]["features"]
    assert [f["properties"]["reportes"] for f in features] == [3]
    assert body["resumen"] == {"sin_agua_vecinos": 3, "periodo_dias": 7, "direccion": "este"}


def test_map_marks_zones_near_drainage_as_floodable(client, engine):
    with Session(engine) as session:
        zone = session.get(Zone, "D9_itocta")
        zone.cerca_drenaje = 28
        session.add(zone)
        session.commit()

    layer = client.get("/zones/D9_itocta/map").json()["capas"]["inundable"]

    assert layer["features"][0]["geometry"] == {
        "type": "Point",
        "coordinates": [-66.2185, -17.4611],
    }
    assert layer["features"][0]["properties"] == {"cerca_drenaje_m": 28, "fuente": "gamc_wms"}


def test_map_history_comes_from_events(client, engine):
    with Session(engine) as session:
        session.add(
            Event(
                tipo="inundacion",
                fecha=datetime(2024, 3, 10).date(),
                zone_id="D9_itocta",
                fuente="eventos_historicos",
            )
        )
        session.commit()

    historial = client.get("/zones/D9_itocta/map").json()["historial"]

    assert historial == [
        {"fecha": "2024-03-10", "tipo": "inundacion", "fuente": "eventos_historicos"}
    ]


def test_map_unknown_zone_returns_404(client):
    assert client.get("/zones/D99_x/map").status_code == 404


def test_map_and_report_follow_the_contract(client):
    created = post(client).json()

    assert contract_errors("ReportCreated", created) == []
    assert contract_errors("ZoneMap", client.get("/zones/D9_itocta/map").json()) == []
