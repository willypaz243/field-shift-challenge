"""ETL GAMC (tarea 1.4): flags por zona desde la API WMS del GAMC.

- GetFeatureInfo por zona (10 zonas × 2 capas: periurbanos + distritos) con rate limit ~12 s.
- Drenaje: FeatureInfo NO está habilitado en el proxy → se muestrea el PNG
  `data/gamc/04/mapas/drenaje_e_influencia.png` (800×512, bbox −66.2807,−17.5312,−66.0459,−17.2573).
- Salida: `data/gamc/zones_gamc.json` con {comuna, distrito, periurbano, es_periurbano,
  cerca_drenaje} por zona.
- Resumible: salta las zonas ya en el JSON de salida.

Uso:
    .venv/bin/python src/etl/gamc_etl.py --out data/gamc/zones_gamc.json
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import requests
from PIL import Image

WMS = "https://serviciosgamc.cochabamba.bo/api/gs/wms"


def _load_key() -> str:
    """Lee GAMC_API_KEY del .env en la raíz del proyecto."""
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

# BBOX del PNG drenaje (GetMap 800×512, EPSG:4326)
DRAIN_PNG = Path("data/gamc/04/mapas/drenaje_e_influencia.png")
DRAIN_BBOX = {"west": -66.2807, "south": -17.5312, "east": -66.0459, "north": -17.2573}
DRAIN_W, DRAIN_H = 800, 512

SLEEP_S = 12  # rate limit medido: ráfaga 8 → 429; 10-15 s → OK


def featureinfo(service: str, lon: float, lat: float) -> dict | None:
    """GetFeatureInfo en (lon, lat) con BBOX ±0.002° (~200 m). Devuelve properties o None."""
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
                print(f"  429 en {service} — espera 30 s")
                time.sleep(30)
                continue
            r.raise_for_status()
            data = r.json()
            features = data.get("features", [])
            if features:
                return features[0].get("properties", {})
            return None
        except Exception as e:
            print(f"  Error {service} intento {attempt + 1}: {e}")
            time.sleep(15)
    return None


def near_drainage(img: Image.Image, lon: float, lat: float) -> bool:
    """¿Hay drenaje en el píxel del PNG para (lon, lat)?"""
    if not (
        DRAIN_BBOX["west"] <= lon <= DRAIN_BBOX["east"]
        and DRAIN_BBOX["south"] <= lat <= DRAIN_BBOX["north"]
    ):
        return False
    px = int((lon - DRAIN_BBOX["west"]) / (DRAIN_BBOX["east"] - DRAIN_BBOX["west"]) * DRAIN_W)
    py = int((DRAIN_BBOX["north"] - lat) / (DRAIN_BBOX["north"] - DRAIN_BBOX["south"]) * DRAIN_H)
    px, py = min(px, DRAIN_W - 1), min(py, DRAIN_H - 1)
    rgba = img.getpixel((px, py))
    return rgba[3] > 0 if len(rgba) == 4 else True  # no transparente → hay drenaje


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/gamc/zones_gamc.json")
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
    print(f"{len(zones)} zonas | ya procesadas: {len(existing)}")

    img = Image.open(DRAIN_PNG).convert("RGBA") if DRAIN_PNG.exists() else None
    if img is None:
        print("WARNING: PNG drenaje no existe; cerca_drenaje=False para todas")

    for i, z in enumerate(zones):
        zid = z["zone_id"]
        if zid in existing:
            print(f"[{i + 1}/{len(zones)}] {zid}: ya procesada")
            continue
        lon, lat = z["lon"], z["lat"]
        print(f"[{i + 1}/{len(zones)}] {zid} ({lon}, {lat})")

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
            "cerca_drenaje": bool(near_drainage(img, lon, lat)) if img else False,
        }
        existing[zid] = result
        out.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
        print(
            f"   comuna={result['comuna']} periurbano={result['periurbano']} "
            f"drenaje={result['cerca_drenaje']}"
        )

    print(f"OK: {len(existing)} zonas en {out}")


if __name__ == "__main__":
    main()
