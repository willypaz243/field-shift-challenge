import json
import sqlite3

import pytest

from api.core.db import make_engine
from src.etl import load_db


@pytest.fixture
def data_root(tmp_path):
    def write(rel, content):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if isinstance(content, str) else json.dumps(content))

    write(
        "data/power/D9_itocta_meta.json",
        {
            "zone_id": "D9_itocta",
            "nombre": "Itocta",
            "lat": -17.4611,
            "lon": -66.2185,
            "elev_m": 3126.04,
        },
    )
    write(
        "data/power/D9_itocta_daily.csv",
        "fecha,tmean,tmin,tmax,t2mdew,rh,ws,ps,pmm,sw,sw_clear,lw\n"
        "2016-01-02,17.0,10.0,24.0,8.0,70.0,2.0,74.0,5.0,21.6,30.0,\n"
        "2016-01-03,9.0,-1.5,20.0,2.0,60.0,2.5,74.0,0.0,22.0,30.0,\n",
    )
    write(
        "data/gamc/zones_gamc.json",
        {
            "D9_itocta": {
                "comuna": "ITOCTA",
                "distrito": "D9",
                "es_periurbano": False,
                "cerca_drenaje_m": 120,
            }
        },
    )
    write("data/srtm/srtm_zones.json", {"D9_itocta": {"elev_m": 2590.0, "slope_deg": 2.1}})
    write(
        "data/crops/crops.json",
        {
            "crops": [
                {
                    "id": "papa",
                    "nombre": "Papa",
                    "ciclo_dias": [120, 180],
                    "kc": {"inicial": 0.75, "medio": 1.15, "final": 1.05},
                    "fix_n": False,
                }
            ]
        },
    )
    write(
        "data/events/events.json",
        {
            "events": [
                {
                    "tipo": "helada",
                    "fecha": "2025-11-17",
                    "zona_id": "D9_itocta",
                    "descripcion": "Helada",
                    "fuente": "prensa",
                }
            ]
        },
    )
    write(
        "data/smap/smap_valle_daily.csv",
        "fecha,sm_surface,sm_root,n_pixels\n2016-01-02,0.3,0.35,35\n",
    )
    write("data/imerg/imerg_valle_daily.csv", "fecha,pmm_imerg,n_pixels\n2016-01-02,4.2,20\n")
    return tmp_path


def query(db, sql):
    with sqlite3.connect(db) as conn:
        return conn.execute(sql).fetchall()


def test_load_fills_tables_from_source_files(data_root, tmp_path):
    db = tmp_path / "valle.db"

    load_db.load(make_engine(f"sqlite:///{db}"), data_root)

    assert query(
        db,
        "SELECT comuna, distrito, elev_m, pendiente, es_agricola, cerca_drenaje, altitud_alta FROM zones",
    ) == [("ITOCTA", "D9", 2590.0, 2.1, 1, 120, 0)]
    assert query(
        db, "SELECT fecha, tmin, sm_surface, pmm_sat FROM climate_history ORDER BY fecha"
    ) == [
        ("2016-01-02", 10.0, 0.3, 4.2),
        ("2016-01-03", -1.5, None, None),
    ]
    assert query(db, "SELECT id, ciclo_min_dias, ciclo_max_dias, kc_inicial FROM crops") == [
        ("papa", 120, 180, 0.75)
    ]
    assert query(db, "SELECT tipo, fecha, zone_id FROM events") == [
        ("helada", "2025-11-17", "D9_itocta")
    ]
    assert query(db, "SELECT id FROM reservoir") == [("angostura",)]


def test_running_load_twice_does_not_duplicate_rows(data_root, tmp_path):
    db = tmp_path / "valle.db"
    engine = make_engine(f"sqlite:///{db}")

    load_db.load(engine, data_root)
    load_db.load(engine, data_root)

    counts = {
        t: query(db, f"SELECT COUNT(*) FROM {t}")[0][0]
        for t in ("zones", "climate_history", "crops", "events", "reservoir")
    }
    assert counts == {"zones": 1, "climate_history": 2, "crops": 1, "events": 1, "reservoir": 1}
