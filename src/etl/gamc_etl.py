"""ETL GAMC (task 1.4): per-zone flags from the GAMC WMS API.

- GetFeatureInfo per zone (10 zones x 2 layers: periurbanos + distritos) with ~12 s rate limit.
- Drainage: FeatureInfo is NOT enabled on the proxy, so the PNG
  `data/gamc/04/mapas/drenaje_e_influencia.png` (800x512, bbox -66.2807,-17.5312,-66.0459,-17.2573)
  is sampled: minimum distance (m) from the zone point to a drainage pixel within 200 m.
- Output: `data/gamc/zones_gamc.json` with {comuna, distrito, periurbano, es_periurbano,
  cerca_drenaje_m} per zone.
- Resumable: skips zones already in the output JSON. `--force-drainage` recomputes
  only the drainage distance (PNG, no WMS calls).

Usage:
    .venv/bin/python -m src.etl.gamc_etl --out data/gamc/zones_gamc.json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path

import requests
from PIL import Image

WMS = "https://serviciosgamc.cochabamba.bo/api/gs/wms"


def _load_key() -> str:
    """Read GAMC_API_KEY from the .env file in the project root."""
    env = Path(__file__).resolve().parents[2] / ".env"
    for line in env.read_text().splitlines():
        if line.startswith("GAMC_API_KEY="):
            return line.split("=", 1)[1].strip()
    return os.environ.get("GAMC_API_KEY", "")


KEY = _load_key()
UUIDS = {
    "periurbanos": "c52066a1-32fd-4925-81e0-c2dcb8f4238f",
    "drenaje": "d4cea6e3-fc7f-482a-94ad-bd377df78886",
    "distritos": "7eb13092-bf0e-493b-aae6-03c43eedda2c",
}

# Drainage PNG bbox (GetMap 800x512, EPSG:4326)
DRAIN_PNG = Path("data/gamc/04/mapas/drenaje_e_influencia.png")
DRAIN_BBOX = {"west": -66.2807, "south": -17.5312, "east": -66.0459, "north": -17.2573}
DRAIN_W, DRAIN_H = 800, 512
DRAIN_RADIUS_M = 200.0
EARTH_M_PER_DEG_LAT = 110_574
EARTH_M_PER_DEG_LON = 111_320

SLEEP_S = 12  # measured rate limit: burst of 8 calls -> 429; 10-15 s -> OK


def featureinfo(service: str, lon: float, lat: float) -> dict | None:
    """GetFeatureInfo at (lon, lat) with a bbox of +/-0.002 deg (~200 m). Returns properties or None."""
    w = 0.002
    params = {
        "key": KEY,
        "service_id": UUIDS[service],
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetFeatureInfo",
        "SRS": "EPSG:4326",
        "BBOX": f"{lon - w},{lat - w},{lon + w},{lat + w}",
        "WIDTH": "256",
        "HEIGHT": "256",
        "X": "128",
        "Y": "128",
        "INFO_FORMAT": "application/json",
        "FEATURE_COUNT": "5",
    }
    for attempt in range(3):
        try:
            r = requests.get(WMS, params=params, timeout=60)
            if r.status_code == 429:
                print(f"  429 on {service} - waiting 30 s")
                time.sleep(30)
                continue
            r.raise_for_status()
            data = r.json()
            features = data.get("features", [])
            if features:
                return features[0].get("properties", {})
            return None
        except Exception as e:
            print(f"  {service} attempt {attempt + 1} error: {e}")
            time.sleep(15)
    return None


def drainage_distance_m(img: Image.Image, lon: float, lat: float) -> int | None:
    """Minimum distance (m) from (lon, lat) to a drainage pixel of the PNG.

    Scans every pixel whose center lies within DRAIN_RADIUS_M. Returns None
    when the point is outside the PNG bbox or no drainage pixel is close
    enough (absence of evidence, not evidence of absence).
    """
    if not (
        DRAIN_BBOX["west"] <= lon <= DRAIN_BBOX["east"]
        and DRAIN_BBOX["south"] <= lat <= DRAIN_BBOX["north"]
    ):
        return None
    m_per_deg_lon = EARTH_M_PER_DEG_LON * math.cos(math.radians(lat))
    deg_w = DRAIN_BBOX["east"] - DRAIN_BBOX["west"]
    deg_h = DRAIN_BBOX["north"] - DRAIN_BBOX["south"]
    mpx_x = deg_w * m_per_deg_lon / DRAIN_W
    mpx_y = deg_h * EARTH_M_PER_DEG_LAT / DRAIN_H
    cx = (lon - DRAIN_BBOX["west"]) / deg_w * DRAIN_W
    cy = (DRAIN_BBOX["north"] - lat) / deg_h * DRAIN_H
    best: float | None = None
    for py in range(
        max(0, int(cy - DRAIN_RADIUS_M / mpx_y) - 1),
        min(DRAIN_H, int(cy + DRAIN_RADIUS_M / mpx_y) + 2),
    ):
        for px in range(
            max(0, int(cx - DRAIN_RADIUS_M / mpx_x) - 1),
            min(DRAIN_W, int(cx + DRAIN_RADIUS_M / mpx_x) + 2),
        ):
            rgba = img.getpixel((px, py))
            if len(rgba) == 4 and rgba[3] == 0:
                continue  # transparent: no drainage
            px_lon = DRAIN_BBOX["west"] + (px + 0.5) * mpx_x / m_per_deg_lon
            px_lat = DRAIN_BBOX["north"] - (py + 0.5) * mpx_y / EARTH_M_PER_DEG_LAT
            dist = math.hypot((px_lon - lon) * m_per_deg_lon, (px_lat - lat) * EARTH_M_PER_DEG_LAT)
            if dist <= DRAIN_RADIUS_M and (best is None or dist < best):
                best = dist
    return None if best is None else int(round(best))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/gamc/zones_gamc.json")
    ap.add_argument(
        "--force-drainage",
        action="store_true",
        help="recompute drainage distance only (PNG, no WMS calls) for all zones",
    )
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if out.exists():
        existing = json.loads(out.read_text())

    zones = []
    for meta in sorted(Path("data/power").glob("*_meta.json")):
        m = json.loads(meta.read_text())
        zones.append(m)
    print(f"{len(zones)} zones | already processed: {len(existing)}")

    img = Image.open(DRAIN_PNG).convert("RGBA") if DRAIN_PNG.exists() else None
    if img is None:
        print("WARNING: drainage PNG not found; cerca_drenaje_m=null for all zones")

    for i, z in enumerate(zones):
        zid = z["zone_id"]
        lon, lat = z["lon"], z["lat"]
        if zid in existing and not args.force_drainage:
            print(f"[{i + 1}/{len(zones)}] {zid}: already processed")
            continue
        print(f"[{i + 1}/{len(zones)}] {zid} ({lon}, {lat})")

        if zid in existing and args.force_drainage:
            result = dict(existing[zid])
            print("   drainage only - no WMS calls")
        else:
            peri = featureinfo("periurbanos", lon, lat)
            time.sleep(SLEEP_S)
            dist = featureinfo("distritos", lon, lat)
            time.sleep(SLEEP_S)
            result = {
                "lat": lat,
                "lon": lon,
                "elev_m": z.get("elev_m"),
                "comuna": (dist or {}).get("Comuna"),
                "distrito": (dist or {}).get("Distrito"),
                "periurbano": (peri or {}).get("Periurbano"),
                "es_periurbano": peri is not None,
            }
        result["cerca_drenaje_m"] = drainage_distance_m(img, lon, lat) if img else None
        result.pop("cerca_drenaje", None)  # legacy boolean key
        existing[zid] = result
        out.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
        print(
            f"   comuna={result.get('comuna')} periurbano={result.get('es_periurbano')} "
            f"drainage_m={result['cerca_drenaje_m']}"
        )

    print(f"OK: {len(existing)} zones in {out}")


if __name__ == "__main__":
    main()
