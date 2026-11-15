import sqlite3

from sqlmodel import Session

from api.core.db import init_db, make_engine
from api.modules.zones.models import Zone
from src.etl import load_forecast

CSV = (
    "fecha,tmean,tmin,tmax,pmm,et0,tmean_baja,tmean_alta,tmin_baja,tmin_alta,pmm_baja,pmm_alta,et0_baja,et0_alta\n"
    "2026-12-31,15.8,9.4,23.7,4.3,4.8,13.0,18.6,5.5,13.3,0.0,15.6,4.2,5.3\n"
    "2027-01-01,15.9,-0.5,23.8,4.4,4.7,13.1,18.7,-2.0,13.4,0.0,15.7,4.1,5.2\n"
)


def setup(tmp_path):
    db = tmp_path / "valle.db"
    engine = make_engine(f"sqlite:///{db}")
    init_db(engine)
    with Session(engine) as session:
        session.add(Zone(id="D9_itocta", lat=-17.46, lon=-66.21))
        session.add(Zone(id="D3_molle", lat=-17.37, lon=-66.19))
        session.commit()
    csv_path = tmp_path / "forecast_valle.csv"
    csv_path.write_text(CSV)
    return db, engine, csv_path


def test_load_forecast_fills_every_zone_with_bands(tmp_path):
    db, engine, csv_path = setup(tmp_path)

    load_forecast.load(engine, csv_path)

    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            "SELECT zone_id, fecha, anio, tmin, tmin_min, tmin_max, pmm_min, pmm_max FROM forecasts "
            "WHERE zone_id='D9_itocta' ORDER BY fecha"
        ).fetchall()
        zones = conn.execute("SELECT COUNT(DISTINCT zone_id) FROM forecasts").fetchone()[0]
    assert rows == [
        ("D9_itocta", "2026-12-31", 2026, 9.4, 5.5, 13.3, 0.0, 15.6),
        ("D9_itocta", "2027-01-01", 2027, -0.5, -2.0, 13.4, 0.0, 15.7),
    ]
    assert zones == 2


def test_reloading_the_forecast_does_not_duplicate_rows(tmp_path):
    db, engine, csv_path = setup(tmp_path)

    load_forecast.load(engine, csv_path)
    load_forecast.load(engine, csv_path)

    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0] == 4
