import sqlite3

from sqlmodel import Session

from api.core.db import init_db, make_engine
from api.modules.zones.models import Zone
from src.etl import load_weather


class Response:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self.body


def daily(first_tmin):
    return {
        "daily": {
            "time": [f"2026-11-{15 + i}" for i in range(9)],
            "temperature_2m_min": [first_tmin] + [5.0] * 8,
            "temperature_2m_max": [24.0] * 9,
            "precipitation_sum": [0.0, 25.8] + [None] + [1.0] * 6,
            "weather_code": [2, 96] + [3] * 7,
        }
    }


def setup(tmp_path):
    db = tmp_path / "valle.db"
    engine = make_engine(f"sqlite:///{db}")
    init_db(engine)
    with Session(engine) as session:
        session.add(Zone(id="D3_molle", lat=-17.37, lon=-66.19))
        session.add(Zone(id="D9_itocta", lat=-17.46, lon=-66.21))
        session.commit()
    return db, engine


def test_load_writes_every_zone_with_hail_and_confidence(tmp_path):
    db, engine = setup(tmp_path)
    calls = []

    def get(url, params, timeout):
        calls.append(params)
        return Response([daily(-1.5), daily(2.0)])

    assert load_weather.load(engine, get) == 16
    assert calls[0]["latitude"] == "-17.37,-17.46"
    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            "SELECT fecha, tmin, pmm, granizo, confianza, fuente FROM weather "
            "WHERE zone_id='D3_molle' ORDER BY fecha"
        ).fetchall()
    assert rows[0] == ("2026-11-15", -1.5, 0.0, 0, "alta", "open_meteo")
    assert rows[1][3] == 1
    assert "2026-11-17" not in [r[0] for r in rows]
    assert [r[4] for r in rows][-1] == "baja"


def test_reloading_replaces_the_forecast(tmp_path):
    db, engine = setup(tmp_path)

    def get(url, params, timeout):
        return Response([daily(1.0), daily(1.0)])

    load_weather.load(engine, get)
    load_weather.load(engine, get)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM weather").fetchone()[0] == 16
        assert conn.execute("SELECT COUNT(*) FROM sync_version").fetchone()[0] == 2


def test_confidence_falls_with_lead_time():
    assert [load_weather.confianza(d) for d in (0, 2, 3, 6, 7, 13)] == [
        "alta",
        "alta",
        "media",
        "media",
        "baja",
        "baja",
    ]
