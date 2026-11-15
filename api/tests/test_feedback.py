import sqlite3

FEEDBACK = {
    "zone_id": "D9_itocta",
    "crop_id": "haba",
    "siembra": "2026-07-15",
    "cosecha": "2026-11-16",
    "resultado": "buena",
}


def rows(engine, sql):
    with sqlite3.connect(engine.url.database) as conn:
        return conn.execute(sql).fetchall()


def test_post_feedback_saves_the_harvest_result(client, engine):
    response = client.post("/feedback", json=FEEDBACK, headers={"Idempotency-Key": "k-1"})

    assert response.status_code == 201
    assert response.json()["id"]
    assert rows(engine, "SELECT zone_id, crop_id, siembra, cosecha, resultado FROM feedback") == [
        ("D9_itocta", "haba", "2026-07-15", "2026-11-16", "buena")
    ]


PLAN = {"zone_id": "D9_itocta", "rotacion_id": "choclo-haba", "siembra": "2027-04-05"}


def test_invalid_resultado_returns_400_with_error_code(client):
    response = client.post(
        "/feedback", json={**FEEDBACK, "resultado": "excelente"}, headers={"Idempotency-Key": "k-1"}
    )

    assert response.status_code == 400
    assert response.json()["error"]["codigo"] == "invalid_request"


def test_unknown_zone_or_crop_returns_404(client):
    unknown_zone = client.post(
        "/feedback", json={**FEEDBACK, "zone_id": "D99_x"}, headers={"Idempotency-Key": "k-1"}
    )
    unknown_crop = client.post(
        "/feedback", json={**FEEDBACK, "crop_id": "kiwi"}, headers={"Idempotency-Key": "k-2"}
    )

    assert (unknown_zone.status_code, unknown_zone.json()["error"]["codigo"]) == (
        404,
        "zone_not_found",
    )
    assert (unknown_crop.status_code, unknown_crop.json()["error"]["codigo"]) == (
        404,
        "crop_not_found",
    )


def test_repeated_idempotency_key_returns_409_with_original_id(client, engine):
    first = client.post("/feedback", json=FEEDBACK, headers={"Idempotency-Key": "k-1"})
    again = client.post("/feedback", json=FEEDBACK, headers={"Idempotency-Key": "k-1"})

    assert again.status_code == 409
    assert again.json()["id"] == first.json()["id"]
    assert rows(engine, "SELECT COUNT(*) FROM feedback") == [(1,)]


def test_post_plan_saves_the_chosen_rotation(client, engine):
    response = client.post("/plans", json=PLAN, headers={"Idempotency-Key": "p-1"})

    assert response.status_code == 201
    assert rows(engine, "SELECT zone_id, rotacion_id, siembra FROM plans") == [
        ("D9_itocta", "choclo-haba", "2027-04-05")
    ]


def test_feedback_and_plan_follow_the_openapi_contract(client):
    from pathlib import Path

    import yaml
    from jsonschema import Draft202012Validator

    spec = yaml.safe_load((Path(__file__).resolve().parents[1] / "openapi.yaml").read_text())
    created_schema = {
        **spec["components"]["schemas"]["Created"],
        "$defs": spec["components"]["schemas"],
    }

    for path, body, key in (("/feedback", FEEDBACK, "c-1"), ("/plans", PLAN, "c-2")):
        operation = spec["paths"][path]["post"]
        header = next(p for p in operation.get("parameters", []) if p["name"] == "Idempotency-Key")
        assert header["in"] == "header" and header["required"] is True
        assert {"201", "409", "400", "404"} <= set(operation["responses"])

        response = client.post(path, json=body, headers={"Idempotency-Key": key})
        assert response.status_code == 201
        assert not list(Draft202012Validator(created_schema).iter_errors(response.json()))


def test_results_by_zone_lists_crop_dates_and_result(client, engine):
    from datetime import date

    from sqlmodel import Session

    from api.modules.feedback.service import results_by_zone

    client.post("/feedback", json=FEEDBACK, headers={"Idempotency-Key": "k-1"})

    with Session(engine) as session:
        results = results_by_zone(session, "D9_itocta")

    assert [(r.crop_id, r.siembra, r.cosecha, r.resultado) for r in results] == [
        ("haba", date(2026, 7, 15), date(2026, 11, 16), "buena")
    ]
