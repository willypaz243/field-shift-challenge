"""Carga a DB SQLite (tarea 1.6): consolida todos los ETL en `data/db/valle.db`.

Tablas (definidas por los modelos SQLModel de `api/modules/*/models.py`):
- zones:          POWER meta + GAMC (comuna/distrito/periurbano/drenaje) + SRTM (elev/pendiente)
- climate_history: POWER diario + SMAP (sm_*, 2015+) + IMERG (pmm_sat, 2016+) + ET₀ Hargreaves
- crops:          data/crops/crops.json
- events:         data/events/events.json (tarea 1.7; vacío si no existe)
- reservoir:      La Angostura (placeholder)
- sync_version:   una versión nueva por carga, para sync delta

Idempotente: upsert por clave primaria; `events` se reemplaza entera. No toca las
tablas que llena la app (reports, feedback, plans).

Uso:
    uv run python -m src.etl.load_db --db data/db/valle.db
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from sqlalchemy import Engine

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.core.db import init_db, make_engine  # noqa: E402
from src.model.et0 import et0_hargreaves  # noqa: E402


def f(v: str | None):
    """str → float o None."""
    v = (v or "").strip()
    return float(v) if v else None


def upsert(con: sqlite3.Connection, table: str, key: tuple[str, ...], rows: list[dict]) -> None:
    if not rows:
        return
    cols = list(rows[0])
    updates = ", ".join(f"{c}=excluded.{c}" for c in cols if c not in key)
    con.executemany(
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(':' + c for c in cols)}) "
        f"ON CONFLICT ({', '.join(key)}) DO UPDATE SET {updates}",
        rows,
    )


def load_zones(con: sqlite3.Connection, root: Path) -> int:
    data = root / "data"
    gamc_json, srtm_json = data / "gamc" / "zones_gamc.json", data / "srtm" / "srtm_zones.json"
    gamc = json.loads(gamc_json.read_text()) if gamc_json.exists() else {}
    srtm = json.loads(srtm_json.read_text()) if srtm_json.exists() else {}
    rows = []
    for meta in sorted((data / "power").glob("*_meta.json")):
        m = json.loads(meta.read_text())
        zid = m["zone_id"]
        g = gamc.get(zid, {})
        s = srtm.get(zid, {})
        elev = s.get("elev_m", m.get("elev_m"))
        rows.append(
            {
                "id": zid,
                "nombre": m.get("nombre"),
                "comuna": g.get("comuna"),
                "distrito": g.get("distrito"),
                "lat": m.get("lat"),
                "lon": m.get("lon"),
                "elev_m": elev,
                "pendiente": s.get("slope_deg"),
                "es_agricola": 0 if g.get("es_periurbano") else 1,
                "cerca_drenaje": 1 if g.get("cerca_drenaje") else 0,
                "altitud_alta": 1 if (elev or 0) >= 2750 else 0,
            }
        )
    upsert(con, "zones", ("id",), rows)
    return len(rows)


def load_climate(con: sqlite3.Connection, root: Path) -> int:
    data = root / "data"
    smap_csv, imerg_csv = (
        data / "smap" / "smap_valle_daily.csv",
        data / "imerg" / "imerg_valle_daily.csv",
    )
    # SMAP e IMERG: series valle (comunes a las 10 zonas — misma celda 0.5°)
    smap: dict[str, tuple] = {}
    if smap_csv.exists():
        with open(smap_csv) as fh:
            for r in csv.DictReader(fh):
                smap[r["fecha"]] = (f(r["sm_surface"]), f(r["sm_root"]))
    imerg: dict[str, float] = {}
    if imerg_csv.exists():
        with open(imerg_csv) as fh:
            for r in csv.DictReader(fh):
                imerg[r["fecha"]] = f(r["pmm_imerg"])
    n_smap = n_imerg = 0

    total = 0
    for csv_path in sorted((data / "power").glob("*_daily.csv")):
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

        def num(a, i):
            return None if np.isnan(a[i]) else float(a[i])

        rows = []
        for i, d in enumerate(fechas):
            sm = smap.get(d)
            ps = imerg.get(d)
            if sm:
                n_smap += 1
            if ps is not None:
                n_imerg += 1
            rows.append(
                {
                    "zone_id": zid,
                    "fecha": d,
                    "tmin": num(tmin, i),
                    "tmax": num(tmax, i),
                    "tmean": num(tmean, i),
                    "pmm": num(pmm_arr, i),
                    "rh": rh[i],
                    "sw": sw[i],
                    "ws": ws[i],
                    "et0": num(et0, i),
                    "sm_surface": sm[0] if sm else None,
                    "sm_root": sm[1] if sm else None,
                    "pmm_sat": ps,
                }
            )
        upsert(con, "climate_history", ("zone_id", "fecha"), rows)
        total += len(rows)
    print(f"  SMAP join: {n_smap} filas | IMERG join: {n_imerg} filas")
    return total


def load_crops(con: sqlite3.Connection, root: Path) -> int:
    d = json.loads((root / "data" / "crops" / "crops.json").read_text())
    rows = []
    for c in d["crops"]:
        tmean_opt = c.get("temp", {}).get("tmean_opt") or [None, None]
        ciclo = c.get("ciclo_dias") or [None, None]
        kc = c.get("kc", {})
        rows.append(
            {
                "id": c["id"],
                "nombre": c["nombre"],
                "t_opt_min": tmean_opt[0],
                "t_opt_max": tmean_opt[1],
                "tol_helada": c.get("helada", {}).get("tolerancia"),
                "demanda_agua": c.get("agua", {}).get("demanda"),
                "deficit_tol": c.get("agua", {}).get("deficit_tol"),
                "ciclo_min_dias": ciclo[0],
                "ciclo_max_dias": ciclo[1],
                "fix_n": 1 if c.get("fix_n") else 0,
                "mercado": c.get("mercado"),
                "breaks_pest_cycle": 1 if c.get("breaks_pest_cycle") else 0,
                "forage_value": c.get("forage_value"),
                "drought_tolerant": c.get("drought_tolerant"),
                "deep_rooting": 1 if c.get("deep_rooting") else 0,
                "erosion_sens": c.get("erosion_sens"),
                "kc_inicial": kc.get("inicial"),
                "kc_medio": kc.get("medio"),
                "kc_final": kc.get("final"),
                "altitud": c.get("altitud"),
                "rotacion": c.get("rotacion"),
                "foto_url": c.get("foto_url"),
            }
        )
    upsert(con, "crops", ("id",), rows)
    return len(rows)


def load_events(con: sqlite3.Connection, root: Path) -> int:
    events_json = root / "data" / "events" / "events.json"
    con.execute("DELETE FROM events")
    if not events_json.exists():
        print("  events: data/events/events.json no existe (tarea 1.7)")
        return 0
    d = json.loads(events_json.read_text())
    rows = [
        {
            "tipo": e.get("tipo"),
            "fecha": e.get("fecha"),
            "zone_id": e.get("zona_id"),
            "descripcion": e.get("descripcion"),
            "fuente": e.get("fuente"),
        }
        for e in d.get("events", [])
    ]
    con.executemany(
        "INSERT INTO events (tipo, fecha, zone_id, descripcion, fuente) "
        "VALUES (:tipo, :fecha, :zone_id, :descripcion, :fuente)",
        rows,
    )
    return len(rows)


def load(engine: Engine, root: Path = ROOT) -> dict[str, int]:
    init_db(engine)
    raw = engine.raw_connection()
    try:
        con = raw.driver_connection
        counts = {
            "zones": load_zones(con, root),
            "climate": load_climate(con, root),
            "crops": load_crops(con, root),
            "events": load_events(con, root),
        }
        # histórico: 27/11/2002 al 5% (ANF) — referencia, no en vivo
        upsert(
            con,
            "reservoir",
            ("id",),
            [
                {
                    "id": "angostura",
                    "nombre": "La Angostura (Riego N°1)",
                    "nivel_pct": 5.0,
                    "volumen_hm3": None,
                    "estado": "historico",
                    "actualizado_en": "2002-11-27",
                }
            ],
        )
        now = datetime.now(UTC).isoformat(timespec="seconds")
        con.execute("INSERT INTO sync_version (creado_en, hash) VALUES (?, ?)", (now, ""))
        con.commit()
    finally:
        raw.close()
    return counts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/db/valle.db")
    args = ap.parse_args()
    db = ROOT / args.db
    counts = load(make_engine(f"sqlite:///{db}"))
    print(
        f"DB {db}: zones={counts['zones']} climate={counts['climate']} "
        f"crops={counts['crops']} events={counts['events']}"
    )


if __name__ == "__main__":
    main()
