#!/usr/bin/env python3
"""
ETL SMAP SPL4SMGP v8 → CSV diario del valle.

Descarga granules globales (148 MB) en paralelo, extrae los píxeles del valle,
calcula el promedio diario y borra el granule. El CSV final es ~300 KB.

Uso:
    .venv/bin/python src/etl/smap_etl.py \
        --start 2015-04-01 --end 2025-12-31 \
        --workers 5 --out data/smap/smap_valle_daily.csv

Resumable: si el CSV ya existe, continúa desde la fecha siguiente.
"""

import argparse
import csv
import hashlib
import io
import json
import logging
import os
import shutil
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from pathlib import Path
from threading import Lock
from xml.etree import ElementTree  # noqa: F401 (not used, kept for future)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("smap_etl")

# ─── Configuración ───────────────────────────────────────────────────────────

CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"
COLLECTION_ID = "C3480440870-NSIDC_CPRD"
BBOX = "-66.40,-17.65,-65.95,-17.15"  # lon_min,lat_min,lon_max,lat_max
TARGET_HOUR_UTC = 16  # granule ~16:30 UTC ≈ 12:30 hora local Cochabamba

# Píxeles del valle (se determinan en runtime desde el primer granule)
VALLE_LAT_MIN = -17.65
VALLE_LAT_MAX = -17.15
VALLE_LON_MIN = -66.40
VALLE_LON_MAX = -65.95

MIN_GRANULE_SIZE = 100 * 1024 * 1024  # 100 MB (sanity check)
MAX_RETRIES = 3
RETRY_BACKOFF = 5  # segundos


# ─── Token ────────────────────────────────────────────────────────────────────


def load_token() -> str:
    """Lee EARTHDATA_TOKEN del .env en la raíz del proyecto."""
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if not env_file.exists():
        raise FileNotFoundError(f".env no encontrado: {env_file}")
    for line in env_file.read_text().splitlines():
        if line.startswith("EARTHDATA_TOKEN="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise ValueError("EARTHDATA_TOKEN no encontrado en .env")


# ─── CMR ──────────────────────────────────────────────────────────────────────


def cmr_query(token: str, params: dict) -> dict:
    """Consulta CMR y devuelve el JSON completo."""
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{CMR_URL}?{qs}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def collect_urls(token: str, start: date, end: date) -> list[tuple[date, str]]:
    """
    Fase 1: consulta CMR mes a mes y devuelve [(fecha, url), ...]
    filtrando el granule más cercano a TARGET_HOUR_UTC.
    """
    urls: list[tuple[date, str]] = []
    cur = start
    while cur <= end:
        # Mes actual
        month_end = min(
            (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
            - timedelta(days=1),
            end,
        )
        temporal = f"{cur.isoformat()}T00:00:00Z,{(month_end + timedelta(days=1)).isoformat()}T00:00:00Z"

        data = cmr_query(
            token,
            {
                "collection_concept_id": COLLECTION_ID,
                "bounding_box": BBOX,
                "temporal": temporal,
                "page_size": "2000",
            },
        )

        entries = data.get("feed", {}).get("entry", [])
        # Agrupar por fecha, elegir el granule más cercano a TARGET_HOUR_UTC
        by_day: dict[str, list[dict]] = {}
        for g in entries:
            pgi = g.get("producer_granule_id", "")
            # Formato: SMAP_L4_SM_gph_YYYYMMDDTHHMMSS_Vv8013_001.h5
            try:
                dt_part = pgi.split("_gph_")[1].split("_")[0]  # YYYYMMDDTHHMMSS
                granule_dt = datetime.strptime(dt_part, "%Y%m%dT%H%M%S")
            except (IndexError, ValueError):
                continue
            day_key = granule_dt.strftime("%Y-%m-%d")
            by_day.setdefault(day_key, []).append((granule_dt, g))

        for day_key in sorted(by_day):
            candidates = by_day[day_key]
            # Elegir el más cercano a TARGET_HOUR_UTC:30
            target = datetime(2000, 1, 1, TARGET_HOUR_UTC, 30)
            best = min(
                candidates,
                key=lambda x: abs(
                    x[0].hour * 3600
                    + x[0].minute * 60
                    - (target.hour * 3600 + target.minute * 60)
                ),
            )
            g = best[1]
            # Extraer URL de descarga
            dl_url = None
            for link in g.get("links", []):
                if "data#" in link.get("rel", "") and ".h5" in link.get("href", ""):
                    dl_url = link["href"]
                    break
            if dl_url:
                d = date.fromisoformat(day_key)
                if start <= d <= end:
                    urls.append((d, dl_url))

        log.info(
            "CMR %s–%s: %d granules → %d días útiles",
            cur.isoformat(),
            month_end.isoformat(),
            len(entries),
            len(by_day),
        )
        cur = month_end + timedelta(days=1)
        time.sleep(0.5)  # polite

    urls.sort(key=lambda x: x[0])
    return urls


# ─── Descarga + Extracción ────────────────────────────────────────────────────


def download_file(token: str, url: str, dest: Path) -> bool:
    """Descarga un granule. True si exitoso."""
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            with open(dest, "wb") as f:
                shutil.copyfileobj(resp, f)
        return dest.stat().st_size >= MIN_GRANULE_SIZE
    except (urllib.error.URLError, OSError) as e:
        log.warning("Download fail: %s", e)
        return False


def extract_valle(granule_path: Path) -> tuple[float, float, int] | None:
    """
    Extrae sm_surface y sm_rootzone para los píxeles del valle.
    Devuelve (sm_surface_mean, sm_rootzone_mean, n_pixels) o None.
    """
    import h5py
    import numpy as np

    try:
        with h5py.File(granule_path, "r") as f:
            lat = f["cell_lat"][:]
            lon = f["cell_lon"][:]
            mask = (
                (lat >= VALLE_LAT_MIN)
                & (lat <= VALLE_LAT_MAX)
                & (lon >= VALLE_LON_MIN)
                & (lon <= VALLE_LON_MAX)
            )
            n_pix = int(mask.sum())
            if n_pix == 0:
                return None
            sm_s = f["Geophysical_Data/sm_surface"][mask]
            sm_r = f["Geophysical_Data/sm_rootzone"][mask]
            s_mean = float(np.nanmean(sm_s))
            r_mean = float(np.nanmean(sm_r))
            return (s_mean, r_mean, n_pix)
    except Exception as e:
        log.warning("Extract fail: %s", e)
        return None


# ─── Worker ───────────────────────────────────────────────────────────────────


def process_one(
    token: str,
    day_url: tuple[date, str],
    tmp_dir: Path,
) -> tuple[date, float, float, int] | None:
    """Descarga, extrae, borra. Devuelve la fila o None."""
    day, url = day_url
    tmp_file = tmp_dir / f"smap_{day.isoformat()}.h5"

    for attempt in range(MAX_RETRIES):
        if not download_file(token, url, tmp_file):
            time.sleep(RETRY_BACKOFF * (attempt + 1))
            continue
        result = extract_valle(tmp_file)
        tmp_file.unlink(missing_ok=True)
        if result is not None:
            return (day, *result)
        # extract falló, reintentar
        time.sleep(RETRY_BACKOFF * (attempt + 1))

    log.error("FAIL %s después de %d intentos", day.isoformat(), MAX_RETRIES)
    return None


# ─── Main ─────────────────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser(description="ETL SMAP → CSV valle")
    ap.add_argument("--start", type=date.fromisoformat, default=date(2015, 4, 1))
    ap.add_argument("--end", type=date.fromisoformat, default=date(2025, 12, 31))
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--out", type=Path, default=Path("data/smap/smap_valle_daily.csv"))
    ap.add_argument(
        "--tmp-dir", type=Path, default=Path(tempfile.gettempdir()) / "smap_etl"
    )
    args = ap.parse_args()

    token = load_token()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.tmp_dir.mkdir(parents=True, exist_ok=True)

    # ── Resumable: leer fechas ya completadas ──
    done: set[date] = set()
    if args.out.exists():
        with open(args.out) as f:
            for row in csv.DictReader(f):
                done.add(date.fromisoformat(row["fecha"]))
        log.info("Resumable: %d días ya completados", len(done))

    # ── Fase 1: CMR ──
    log.info(
        "Fase 1: consulta CMR %s → %s", args.start.isoformat(), args.end.isoformat()
    )
    all_urls = collect_urls(token, args.start, args.end)
    log.info("Fase 1 completa: %d URLs", len(all_urls))

    # Filtrar los que faltan
    pending = [(d, u) for d, u in all_urls if d not in done]
    log.info("Pendientes: %d días", len(pending))

    if not pending:
        log.info("Nada que hacer. CSV completo.")
        return

    # ── Fase 2: descarga paralela ──
    csv_lock = Lock()
    completed = 0
    failed = 0
    start_time = time.time()

    # Abrir CSV en append
    write_header = not args.out.exists() or args.out.stat().st_size == 0
    csv_file = open(args.out, "a", newline="")
    writer = csv.writer(csv_file)
    if write_header:
        writer.writerow(["fecha", "sm_surface", "sm_root", "n_pixels"])
        csv_file.flush()

    def worker(item):
        nonlocal completed, failed
        result = process_one(token, item, args.tmp_dir)
        with csv_lock:
            if result:
                writer.writerow(
                    [
                        result[0].isoformat(),
                        f"{result[1]:.6f}",
                        f"{result[2]:.6f}",
                        result[3],
                    ]
                )
                csv_file.flush()
                completed += 1
            else:
                failed += 1
            if completed % 50 == 0 and completed > 0:
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta_h = (
                    (len(pending) - completed - failed) / rate / 3600 if rate > 0 else 0
                )
                log.info(
                    "Progress: %d/%d done | %d fail | %.1f d/h | ETA %.1f h",
                    completed,
                    len(pending),
                    failed,
                    rate,
                    eta_h,
                )

    log.info("Fase 2: %d workers, %d días pendientes", args.workers, len(pending))
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(worker, item): item for item in pending}
        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception as e:
                failed += 1
                log.error("Worker exception: %s", e)

    csv_file.close()

    elapsed = time.time() - start_time
    log.info(
        "FIN: %d OK, %d fail, %d min totales. CSV: %s (%d bytes)",
        completed,
        failed,
        round(elapsed / 60, 1),
        args.out,
        args.out.stat().st_size,
    )

    # Limpieza tmp
    shutil.rmtree(args.tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
