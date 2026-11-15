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
