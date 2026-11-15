"""ETL SRTM/DEM (tarea 1.5): elevación + pendiente por zona.

Fuente: Open-Meteo Elevation API (sin API key, basado en DEM global ~30 m).
- 2 requests por zona: cuadrícula 3×3 a 33 m (elevación, P15 = piso de valle)
  + cuadrícula 7×7 a 150 m (pendiente por bordes, menos ruido DEM).
- Salida: `data/srtm/srtm_zones.json` {zona: {elev_m, slope_deg, grid}}.
- Resumible: salta zonas ya en la salida.

Nota: el servidor USGS/CGIAR de SRTM 90 m ya no responde (404); Open-Meteo
cubre el mismo dato (elevation) con mejor disponibilidad. La cota 2750 m del
GAMC se compara contra `elev_m`.

Uso:
    .venv/bin/python src/etl/srtm_etl.py --out data/srtm/srtm_zones.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests

API = "https://api.open-meteo.com/v1/elevation"
STEP_ELEV = 0.0003  # ~33 m (elevación de punto, 3×3)
STEP_SLOPE = 0.0015  # ~150 m (pendiente, 7×7 → menos ruido DEM)
COS_LAT = 0.77  # cos(17.4°)


def query_grid(lat: float, lon: float, n: int, step: float) -> list[list[float]]:
    """Cuadrícula n×n de elevaciones (N→S, O→E)."""
    lats = [lat + step * ((n - 1) / 2 - i) for i in range(n)]
    lons = [lon + step * (j - (n - 1) / 2) for j in range(n)]
    params = {
        "latitude": ",".join(f"{v:.6f}" for v in lats * n),
        "longitude": ",".join(f"{v:.6f}" for v in lons for _ in range(n)),
    }
    r = requests.get(API, params=params, timeout=30)
    r.raise_for_status()
    elevs = r.json()["elevation"]
    return [elevs[i * n : (i + 1) * n] for i in range(n)]


def slope_deg(grid: list[list[float]], step: float) -> float:
    """Pendiente (°) por diferencias de bordes N-S / E-O (promediados)."""
    import math

    n = len(grid)
    north = sum(grid[0]) / n
    south = sum(grid[-1]) / n
    west = sum(row[0] for row in grid) / n
    east = sum(row[-1] for row in grid) / n
    dz_dy = (north - south) / ((n - 1) * step * 111_000)
    dz_dx = (east - west) / ((n - 1) * step * 111_000 * COS_LAT)
    return math.degrees(math.atan(math.hypot(dz_dx, dz_dy)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/srtm/srtm_zones.json")
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if out.exists():
        existing = json.loads(out.read_text())

    zones = [json.loads(m.read_text()) for m in sorted(Path("data/power").glob("*_meta.json"))]
    print(f"{len(zones)} zonas | ya procesadas: {len(existing)}")

    for i, z in enumerate(zones):
        zid = z["zone_id"]
        if zid in existing:
            print(f"[{i + 1}/{len(zones)}] {zid}: ya procesada")
            continue
        lat, lon = z["lat"], z["lon"]
        for attempt in range(3):
            try:
                grid = query_grid(lat, lon, 3, STEP_ELEV)
                grid_slope = query_grid(lat, lon, 7, STEP_SLOPE)
                break
            except Exception as e:
                print(f"  Error {zid} intento {attempt + 1}: {e}")
                time.sleep(5)
        else:
            continue
        # P15 de la cuadrícula = piso de valle (evita cumbres en celdas de ladera)
        vals = sorted(v for row in grid for v in row)
        elev = vals[int(0.15 * (len(vals) - 1))]
        existing[zid] = {
            "lat": lat,
            "lon": lon,
            "elev_m": round(elev, 1),
            "elev_centro_m": round(grid[1][1], 1),
            "slope_deg": round(slope_deg(grid_slope, STEP_SLOPE), 2),
            "grid_m": grid,
            "sobre_cota_2750": elev >= 2750,
        }
        out.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
        print(
            f"[{i + 1}/{len(zones)}] {zid}: elev={elev:.0f} m slope={existing[zid]['slope_deg']:.1f}°"
        )
        time.sleep(1)

    print(f"OK: {len(existing)} zonas en {out}")


if __name__ == "__main__":
    main()
