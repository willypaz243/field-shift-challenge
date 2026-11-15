"""Carga a DB SQLite (tarea 1.6): consolida todos los ETL en `data/db/valle.db`.

Tablas (schema BACKLOG §5):
- zones:          POWER meta + GAMC (comuna/distrito/periurbano/drenaje) + SRTM (elev/pendiente)
- climate_history: POWER diario + SMAP (sm_*, 2015+) + IMERG (pmm_sat, 2016+) + ET₀ Hargreaves
- crops:          data/crops/crops.json
- events:         data/events/events.json (tarea 1.7; vacío si no existe)
- reservoir:      La Angostura (placeholder)
- forecasts/reports: vacías (Fases 3–4)
- sync_version:   versión inicial para sync delta

Idempotente: DROP + recrear tablas y recargar todo (datos determinísticos).
La DB queda lista para la API (Fase 3) sin depender de los CSV en runtime.

Uso:
    .venv/bin/python src/etl/load_db.py --db data/db/valle.db
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.model.et0 import et0_hargreaves  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
POWER_DIR = ROOT / "data" / "power"
GAMC_JSON = ROOT / "data" / "gamc" / "zones_gamc.json"
SRTM_JSON = ROOT / "data" / "srtm" / "srtm_zones.json"
CROPS_JSON = ROOT / "data" / "crops" / "crops.json"
EVENTS_JSON = ROOT / "data" / "events" / "events.json"
SMAP_CSV = ROOT / "data" / "smap" / "smap_valle_daily.csv"
IMERG_CSV = ROOT / "data" / "imerg" / "imerg_valle_daily.csv"

SCHEMA = """
DROP TABLE IF EXISTS zones;
DROP TABLE IF EXISTS climate_history;
DROP TABLE IF EXISTS crops;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS reservoir;
DROP TABLE IF EXISTS forecasts;
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS sync_version;

CREATE TABLE zones (
    id TEXT PRIMARY KEY,
    nombre TEXT, comuna TEXT, distrito TEXT,
    lat REAL, lon REAL, elev_m REAL, pendiente REAL,
    es_agricola INTEGER,          -- 1 si NO periurbano (mask GAMC)
    cerca_drenaje INTEGER,        -- 1/0 (binaria; distancia exacta = brecha)
    altitud_alta INTEGER          -- 1 si elev > 2750 m
);

CREATE TABLE climate_history (
    zone_id TEXT, fecha TEXT,
    tmin REAL, tmax REAL, tmean REAL, pmm REAL, rh REAL, sw REAL, ws REAL,
    et0 REAL,                     -- ET₀ Hargreaves FAO-56 (mm/día)
    sm_surface REAL, sm_root REAL,-- SMAP (2015+)
    pmm_sat REAL,                 -- IMERG GPM (2016+), validación cruzada
    PRIMARY KEY (zone_id, fecha)
);
CREATE INDEX idx_climate_fecha ON climate_history(fecha);

CREATE TABLE crops (
    id TEXT PRIMARY KEY, nombre TEXT, t_opt_min REAL, t_opt_max REAL,
    tol_helada TEXT, demanda_agua TEXT, deficit_tol TEXT, ciclos_dias TEXT,
    fix_n INTEGER, mercado TEXT, breaks_pest_cycle INTEGER, forage_value TEXT,
    drought_tolerant TEXT, deep_rooting INTEGER, erosion_sens TEXT,
    kcInicial REAL, kcMedio REAL, kcFinal REAL,
    altitud TEXT, rotacion TEXT, foto_url TEXT
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT, fecha TEXT, zona_id TEXT, descripcion TEXT, fuente TEXT
);

CREATE TABLE reservoir (
    id TEXT PRIMARY KEY, nombre TEXT, nivel_pct REAL, volumen_hm3 REAL,
    estado TEXT, actualizado_en TEXT
);

CREATE TABLE forecasts (
    zone_id TEXT, anio INTEGER, fecha TEXT,
    tmin REAL, tmax REAL, tmean REAL, pmm REAL, et0 REAL,
    incert_min REAL, incert_max REAL, creado_en TEXT,
    PRIMARY KEY (zone_id, fecha)
);

CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parcela_id TEXT, tipo TEXT, fecha TEXT, foto_url TEXT, audio_url TEXT,
    enviado_en TEXT
);

CREATE TABLE sync_version (id TEXT PRIMARY KEY, creado_en TEXT, hash TEXT);
"""


def f(v: str | None):
    """str → float o None."""
    v = (v or "").strip()
    return float(v) if v else None


def load_zones(con: sqlite3.Connection) -> int:
    gamc = json.loads(GAMC_JSON.read_text()) if GAMC_JSON.exists() else {}
    srtm = json.loads(SRTM_JSON.read_text()) if SRTM_JSON.exists() else {}
    rows = []
    for meta in sorted(POWER_DIR.glob("*_meta.json")):
        m = json.loads(meta.read_text())
        zid = m["zone_id"]
        g = gamc.get(zid, {})
        s = srtm.get(zid, {})
        elev = s.get("elev_m", m.get("elev_m"))
        rows.append(
            (
                zid,
                m.get("nombre"),
                g.get("comuna"),
                g.get("distrito"),
                m.get("lat"),
                m.get("lon"),
                elev,
                s.get("slope_deg"),
                0 if g.get("es_periurbano") else 1,
                1 if g.get("cerca_drenaje") else 0,
                1 if (elev or 0) >= 2750 else 0,
            )
        )
    con.executemany("INSERT INTO zones VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)


def load_climate(con: sqlite3.Connection) -> int:
    # SMAP e IMERG: series valle (comunes a las 10 zonas — misma celda 0.5°)
    smap: dict[str, tuple] = {}
    if SMAP_CSV.exists():
        with open(SMAP_CSV) as fh:
            for r in csv.DictReader(fh):
                smap[r["fecha"]] = (f(r["sm_surface"]), f(r["sm_root"]))
    imerg: dict[str, float] = {}
    if IMERG_CSV.exists():
        with open(IMERG_CSV) as fh:
            for r in csv.DictReader(fh):
                imerg[r["fecha"]] = f(r["pmm_imerg"])
    n_smap = n_imerg = 0

    total = 0
    for csv_path in sorted(POWER_DIR.glob("*_daily.csv")):
        zid = csv_path.name.replace("_daily.csv", "")
        fechas, tmean, tmin, tmax, pmm, rh, sw, ws = [], [], [], [], [], [], [], []
        with open(csv_path) as fh:
            for r in csv.DictReader(fh):
                fechas.append(r["fecha"])
                tmean.append(f(r["tmean"]))
                tmin.append(f(r["tmin"]))
                tmax.append(f(r["tmax"]))
                pmm.append(f(r["pmm"]))
                rh.append(f(r["rh"]))
                sw.append(f(r["sw"]))
                ws.append(f(r["ws"]))
        tmean = np.array(tmean, dtype=float)
        tmin = np.array(tmin, dtype=float)
        tmax = np.array(tmax, dtype=float)
        # pmm > 100 mm/día = error de dato POWER → NaN (ver EDA.md)
        pmm_arr = np.array([None if (v is not None and v > 100) else v for v in pmm], dtype=float)
        doy = np.array(
            [(datetime.strptime(d, "%Y-%m-%d").timetuple().tm_yday) for d in fechas],
            dtype=float,
        )
        et0 = et0_hargreaves(tmean, tmax, tmin, doy)

        rows = []
        for i, d in enumerate(fechas):
            sm = smap.get(d)
            ps = imerg.get(d)
            if sm:
                n_smap += 1
            if ps is not None:
                n_imerg += 1
            rows.append(
                (
                    zid,
                    d,
                    None if np.isnan(tmin[i]) else tmin[i],
                    None if np.isnan(tmax[i]) else tmax[i],
                    None if np.isnan(tmean[i]) else tmean[i],
                    None if np.isnan(pmm_arr[i]) else pmm_arr[i],
                    rh[i] if rh[i] is not None else None,
                    sw[i] if sw[i] is not None else None,
                    ws[i] if ws[i] is not None else None,
                    None if np.isnan(et0[i]) else float(et0[i]),
                    sm[0] if sm else None,
                    sm[1] if sm else None,
                    ps,
                )
            )
        con.executemany("INSERT INTO climate_history VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        total += len(rows)
    print(f"  SMAP join: {n_smap} filas | IMERG join: {n_imerg} filas")
    return total


def load_crops(con: sqlite3.Connection) -> int:
    d = json.loads(CROPS_JSON.read_text())
    rows = []
    for c in d["crops"]:
        temp = c.get("temp", {})
        rows.append(
            (
                c["id"],
                c["nombre"],
                temp.get("tmean_opt", [None, None])[0],
                temp.get("tmean_opt", [None, None])[1],
                c.get("helada", {}).get("tolerancia"),
                c.get("agua", {}).get("demanda"),
                c.get("agua", {}).get("deficit_tol"),
                json.dumps(c.get("ciclo_dias")),
                1 if c.get("fix_n") else 0,
                c.get("mercado"),
                1 if c.get("breaks_pest_cycle") else 0,
                c.get("forage_value"),
                c.get("drought_tolerant"),
                1 if c.get("deep_rooting") else 0,
                c.get("erosion_sens"),
                c.get("kc", {}).get("inicial"),
                c.get("kc", {}).get("medio"),
                c.get("kc", {}).get("final"),
                c.get("altitud"),
                c.get("rotacion"),
                c.get("foto_url"),
            )
        )
    con.executemany("INSERT INTO crops VALUES (" + ",".join(["?"] * 21) + ")", rows)
    return len(rows)


def load_events(con: sqlite3.Connection) -> int:
    if not EVENTS_JSON.exists():
        print("  events: data/events/events.json no existe (tarea 1.7)")
        return 0
    d = json.loads(EVENTS_JSON.read_text())
    rows = [
        (
            e.get("tipo"),
            e.get("fecha"),
            e.get("zona_id"),
            e.get("descripcion"),
            e.get("fuente"),
        )
        for e in d.get("events", [])
    ]
    con.executemany(
        "INSERT INTO events (tipo,fecha,zona_id,descripcion,fuente) VALUES (?,?,?,?,?)",
        rows,
    )
    return len(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/db/valle.db")
    args = ap.parse_args()
    db = ROOT / args.db
    db.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(db)
    con.executescript(SCHEMA)

    n_zones = load_zones(con)
    n_clim = load_climate(con)
    n_crops = load_crops(con)
    n_events = load_events(con)

    con.execute(
        "INSERT INTO reservoir VALUES (?,?,?,?,?,?)",
        (
            "angostura",
            "La Angostura (Riego N°1)",
            5.0,  # histórico: 27/11/2002 al 5% (ANF) — referencia, no en vivo
            None,
            "historico",
            "2002-11-27",
        ),
    )
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    con.execute("INSERT INTO sync_version VALUES (?,?,?)", ("1", now, ""))
    con.commit()

    print(
        f"DB {db}: zones={n_zones} climate={n_clim} crops={n_crops} "
        f"events={n_events} | creado {now}"
    )
    con.close()


if __name__ == "__main__":
    main()
