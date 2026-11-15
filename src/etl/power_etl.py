#!/usr/bin/env python3
"""
ETL — NASA POWER (Power-DA) → CSV por zona, listo para la tabla `climate_history`.

Verificado en vivo el 14/11/2026 (API v2.10.3):
- **NO requiere token** (la API responde sin `token` ni con uno inválido).
- `start`/`end` = entero YYYYMMDD. Rango: 1984 → presente.
- `community=ag` (minúscula). Parámetros válidos en diario:
  T2M, T2MDEW, RH2M, WS2M, PS, PRECTOT (→PRECTOTCORR), TS,
  ALLSKY_SFC_SW_DWN, ALLSKY_SFC_LW_DWN, CLRSKY_SFC_SW_DWN.
- **Sin T2MIN/T2MAX en diario** → se derivan de hourly `T2M` (8760 h/año).

Uso:
    python3 power_etl.py                     # usa points.json del mismo directorio
    python3 power_etl.py --points mi.json    # lista de puntos propia
    python3 power_etl.py --start 1984 --end 2025 --out /ruta/salida

Salida (por punto):
    {out}/{zone_id}_daily.csv   fecha,tmean,tmin,tmax,t2mdew,rh,ws,ps,pmm,sw,sw_clear,lw
    {out}/{zone_id}_meta.json   lat, lon, elev_m, rango, n_filas

Sin dependencias externas (solo stdlib).
"""

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

API = "https://power.larc.nasa.gov/api/temporal"
DAILY_PARAMS = (
    "T2M,T2MDEW,RH2M,WS2M,PS,PRECTOT,TS,ALLSKY_SFC_SW_DWN,ALLSKY_SFC_LW_DWN,CLRSKY_SFC_SW_DWN"
)
FILL = -999.0

# Mapeo parámetro API → columna CSV
COLS = [
    ("tmean", "T2M"),
    ("t2mdew", "T2MDEW"),
    ("rh", "RH2M"),
    ("ws", "WS2M"),
    ("ps", "PS"),
    ("pmm", "PRECTOTCORR"),
    ("ts", "TS"),
    ("sw", "ALLSKY_SFC_SW_DWN"),
    ("lw", "ALLSKY_SFC_LW_DWN"),
    ("sw_clear", "CLRSKY_SFC_SW_DWN"),
]
PARAM_TO_COL = {param: col for col, param in COLS}


def fetch(url: str, retries: int = 3, wait: int = 5) -> dict[str, Any]:
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if attempt == retries:
                raise
            print(f"  WARN {e} — reintento {attempt}/{retries} en {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError("unreachable: the final attempt always raises")


def chunk_years(start: int, end: int):
    for y in range(start, end + 1):
        yield y * 10000 + 101, (y + 1) * 10000 + 101


def download_daily(lat, lon, start, end):
    """→ ({fecha: {col: val}}, elev_m)"""
    out = {}
    elev = None
    for s, e in chunk_years(start, end):
        url = (
            f"{API}/daily/point?latitude={lat}&longitude={lon}"
            f"&start={s}&end={e}&parameters={DAILY_PARAMS}&community=ag&format=JSON"
        )
        d = fetch(url)
        if elev is None:
            elev = d["geometry"]["coordinates"][2]
        for key, series in d["properties"]["parameter"].items():
            col = PARAM_TO_COL.get(key)
            if col is None:
                continue
            for f, v in series.items():
                out.setdefault(f, {})[col] = None if v == FILL else v
        print(f"  diario {s}–{e} OK", file=sys.stderr)
    return out, elev


def derive_minmax(hourly: dict[str, Any]):
    """hourly {YYYYMMDDHH: val} → {fecha: (tmin, tmax)}"""
    days = defaultdict(list)
    for k, v in hourly.items():
        if v != FILL:
            days[k[:8]].append(v)
    return {f: (min(x), max(x)) for f, x in days.items()}


def download_hourly_t2m(lat, lon, start, end):
    out = {}
    for s, e in chunk_years(start, end):
        url = (
            f"{API}/hourly/point?latitude={lat}&longitude={lon}"
            f"&start={s}&end={e}&parameters=T2M&community=ag&format=JSON"
        )
        d = fetch(url)
        out.update(d["properties"]["parameter"]["T2M"])
        print(f"  hourly {s}–{e} OK", file=sys.stderr)
    return out


def write_zone(z, start, end, hstart, hend, outdir: Path):
    lat, lon = z["lat"], z["lon"]
    print(f"▶ zona {z['id']} ({lat}, {lon})", file=sys.stderr)
    daily, elev = download_daily(lat, lon, start, end)
    hourly = download_hourly_t2m(lat, lon, hstart, hend)
    minmax = derive_minmax(hourly)

    rows = []
    for f in sorted(daily):
        d = daily[f]
        mn, mx = minmax.get(f, (None, None))
        rows.append(
            {
                "fecha": f"{f[0:4]}-{f[4:6]}-{f[6:8]}",
                "tmean": d.get("tmean"),
                "tmin": mn,
                "tmax": mx,
                "t2mdew": d.get("t2mdew"),
                "rh": d.get("rh"),
                "ws": d.get("ws"),
                "ps": d.get("ps"),
                "pmm": d.get("pmm"),
                "sw": d.get("sw"),
                "sw_clear": d.get("sw_clear"),
                "lw": d.get("lw"),
            }
        )

    csv_path = outdir / f"{z['id']}_daily.csv"
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    meta = {
        "zone_id": z["id"],
        "nombre": z.get("nombre", ""),
        "lat": lat,
        "lon": lon,
        "elev_m": elev,
        "start": start,
        "end": end,
        "hstart": hstart,
        "hend": hend,
        "filas": len(rows),
    }
    (outdir / f"{z['id']}_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"  ✔ {csv_path} ({len(rows)} filas)", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", default=str(Path(__file__).parent / "points.json"))
    ap.add_argument("--start", type=int, default=1984)
    ap.add_argument("--end", type=int, default=2025)
    ap.add_argument("--hstart", type=int, default=None, help="año inicio hourly (def: start)")
    ap.add_argument("--hend", type=int, default=None, help="año fin hourly (def: end)")
    ap.add_argument("--out", default=str(Path(__file__).parent.parent.parent / "data" / "power"))
    a = ap.parse_args()
    a.hstart = a.hstart or a.start
    a.hend = a.hend or a.end

    points = json.loads(Path(a.points).read_text())
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    for z in points:
        write_zone(z, a.start, a.end, a.hstart, a.hend, outdir)
    print("DONE", file=sys.stderr)


if __name__ == "__main__":
    main()
