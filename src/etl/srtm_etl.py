"""SRTM/DEM ETL (task 1.5): elevation + slope per zone.

Source: Open-Meteo Elevation API (no API key, based on a ~30 m global DEM).
- 2 requests per zone: 3x3 grid at 33 m (elevation, P15 = valley floor)
  + 7x7 grid at 150 m (slope from edges, less DEM noise).
- Output: `data/srtm/srtm_zones.json` {zone: {elev_m, slope_deg, grid}}.
- Resumable: skips zones already in the output.

Note: the real source is the Open-Meteo Elevation API (~30 m global DEM), not
a direct NASA SRTM download: the USGS/CGIAR SRTM 90 m server no longer
responds (404) and Open-Meteo covers the same data with better availability.
The name "srtm" is kept for pipeline continuity.
The GAMC 2750 m threshold is compared against `elev_m`.

Usage:
    .venv/bin/python -m src.etl.srtm_etl --out data/srtm/srtm_zones.json
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import requests

API = "https://api.open-meteo.com/v1/elevation"
STEP_ELEV = 0.0003  # ~33 m (point elevation, 3x3)
STEP_SLOPE = 0.0015  # ~150 m (slope, 7x7 -> less DEM noise)
EARTH_M_PER_DEG = 111_000


def query_grid(lat: float, lon: float, n: int, step: float) -> list[list[float]]:
    """n x n grid of elevations (N->S, W->E)."""
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


def slope_deg(grid: list[list[float]], step: float, cos_lat: float) -> float:
    """Slope (deg) from averaged N-S / E-W edge differences.

    `cos_lat` scales the east-west distance at the zone latitude.
    """
    n = len(grid)
    north = sum(grid[0]) / n
    south = sum(grid[-1]) / n
    west = sum(row[0] for row in grid) / n
    east = sum(row[-1] for row in grid) / n
    dz_dy = (north - south) / ((n - 1) * step * EARTH_M_PER_DEG)
    dz_dx = (east - west) / ((n - 1) * step * EARTH_M_PER_DEG * cos_lat)
    return math.degrees(math.atan(math.hypot(dz_dx, dz_dy)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/srtm/srtm_zones.json")
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    if out.exists():
        existing = json.loads(out.read_text())

    zones = [json.loads(m.read_text()) for m in sorted(Path("data/power").glob("*_meta.json"))]
    print(f"{len(zones)} zones | already processed: {len(existing)}")

    for i, z in enumerate(zones):
        zid = z["zone_id"]
        if zid in existing:
            print(f"[{i + 1}/{len(zones)}] {zid}: already processed")
            continue
        lat, lon = z["lat"], z["lon"]
        for attempt in range(3):
            try:
                grid = query_grid(lat, lon, 3, STEP_ELEV)
                grid_slope = query_grid(lat, lon, 7, STEP_SLOPE)
                break
            except Exception as e:
                print(f"  {zid} attempt {attempt + 1} error: {e}")
                time.sleep(5)
        else:
            continue
        # P15 of the grid = valley floor (avoids ridge peaks in hillside cells)
        vals = sorted(v for row in grid for v in row)
        elev = vals[int(0.15 * (len(vals) - 1))]
        existing[zid] = {
            "lat": lat,
            "lon": lon,
            "elev_m": round(elev, 1),
            "elev_centro_m": round(grid[1][1], 1),
            "slope_deg": round(slope_deg(grid_slope, STEP_SLOPE, math.cos(math.radians(lat))), 2),
            "grid_m": grid,
            "sobre_cota_2750": elev >= 2750,
        }
        out.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
        print(
            f"[{i + 1}/{len(zones)}] {zid}: elev={elev:.0f} m slope={existing[zid]['slope_deg']:.1f}°"
        )
        time.sleep(1)

    print(f"OK: {len(existing)} zones in {out}")


if __name__ == "__main__":
    main()
