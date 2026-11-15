#!/usr/bin/env python3
"""
ETL GPM_3IMERGDL v07 — precipitación diaria del valle (Cochabamba).

- Consulta CMR por mes (concept-id=C2723754859-GES_DISC).
- Descarga granules NetCDF4 globales (~1/día).
- Extrae `precipitation` (mm/hr, 24 valores) → suma diaria → promedio por píxeles del valle.
- Salida CSV: fecha, pmm_imerg, n_pixels
- Resumible: salta fechas ya en el CSV.
- Workers paralelos (descarga + extracción).

Uso:
    .venv/bin/python src/etl/imerg_etl.py --start 2016-01-01 --end 2025-12-31 --workers 3 --out data/smap/imerg_valle_daily.csv
"""

import argparse
import csv
import logging
import os
import re
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import requests

# ─── Config ───────────────────────────────────────────────────────────────────

CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"
COLLECTION_ID = "C2723754859-GES_DISC"  # GPM_3IMERGDL v07

# BBOX valle de Cochabamba (WGS84)
BBOX = {
    "west": -66.40,
    "south": -17.65,
    "east": -65.95,
    "north": -17.15,
}

# Resolución IMERG: 0.1° → píxeles esperados en el bbox
# lon: 0.45° / 0.1° = 4.5 → ~5 cols
# lat: 0.50° / 0.1° = 5.0 → ~5 rows
# ~25 píxeles (algunos parciales)
EXPECTED_PIXELS = 25

# HDF5/NetCDF4 NO es thread-safe: la extracción se serializa (la descarga sí corre en paralelo)
NC_LOCK = threading.Lock()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("imerg_etl")


# ─── Token ────────────────────────────────────────────────────────────────────


def load_token() -> str:
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("EARTHDATA_TOKEN="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("EARTHDATA_TOKEN", "")


# ─── CMR ──────────────────────────────────────────────────────────────────────


def query_cmr_month(token: str, year: int, month: int) -> list[dict]:
    """Devuelve lista de {date, url} para un mes."""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    params = {
        "concept-id": COLLECTION_ID,
        "temporal": f"{start.isoformat()}T00:00:00Z,{end.isoformat()}T00:00:00Z",
        "bounding_box": f"{BBOX['west']},{BBOX['south']},{BBOX['east']},{BBOX['north']}",
        "provider": "GES_DISC",
        "page_size": "500",  # CMR ya no usa `limit`; default = 10 granules
    }
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    resp = requests.get(CMR_URL, params=params, headers=headers, timeout=60)
    resp.raise_for_status()
    entries = resp.json().get("feed", {}).get("entry", [])

    results = []
    for e in entries:
        title = e.get("producer_granule_id", "") or e.get("title", "")
        # Formato: 3B-DAY-L.MS.MRG.3IMERG.20251101-S000000-E235959.V07B
        m = re.search(r"3IMERG\.(\d{8})-S", title)
        if not m:
            continue
        granule_date = datetime.strptime(m.group(1), "%Y%m%d").date()
        # Solo días dentro del mes
        if not (start <= granule_date < end):
            continue
        # Buscar URL de descarga
        url = None
        for link in e.get("links", []):
            if link.get("rel", "").endswith("data#"):
                url = link["href"]
                break
        if url:
            results.append({"date": granule_date, "url": url})

    return results


# ─── Descarga + Extracción ────────────────────────────────────────────────────


def download_and_extract(
    date_str: str, url: str, token: str, tmp_dir: Path
) -> tuple[str, float, int] | None:
    """Descarga el granule, extrae precipitación diaria del valle. Devuelve (fecha, pmm, n_pixels) o None."""
    filepath = tmp_dir / f"imerg_{date_str}.nc4"

    # Descargar
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        with requests.get(
            url, headers=headers, stream=True, timeout=300, allow_redirects=True
        ) as r:
            r.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    f.write(chunk)
    except Exception as e:
        log.warning(f"Download fail {date_str}: {e}")
        filepath.unlink(missing_ok=True)
        return None

    # Extraer (HDF5 no es thread-safe: serializar el acceso al archivo)
    try:
        import netCDF4

        with NC_LOCK:
            ds = netCDF4.Dataset(str(filepath), "r")
            # Shape real: (time=1, lon=3600, lat=1800) — ya es total diario (mm)
            precip = ds.variables["precipitation"][:]
            lats = ds.variables["lat"][:]
            lons = ds.variables["lon"][:]
            ds.close()

        # Mask del valle: (lon, lat)
        lon_mask = (lons >= BBOX["west"]) & (lons <= BBOX["east"])
        lat_mask = (lats >= BBOX["south"]) & (lats <= BBOX["north"])
        pixel_mask = np.outer(lon_mask, lat_mask)  # (lon=3600, lat=1800)

        n_pixels = int(pixel_mask.sum())
        if n_pixels == 0:
            log.warning(f"{date_str}: 0 píxeles en bbox")
            return None

        # Tomar el día único (time=0) → (lon, lat)
        daily = precip[0]
        valley_pixels = daily[pixel_mask]
        # Filtrar valores no válidos (NetCDF fill = -9999 o NaN)
        valid = valley_pixels[~np.isnan(valley_pixels) & (valley_pixels > -9000)]
        if len(valid) == 0:
            return None
        pmm_daily = float(valid.mean())

        return (date_str, pmm_daily, n_pixels)

    except Exception as e:
        log.warning(f"Extract fail {date_str}: {e}")
        return None
    finally:
        filepath.unlink(missing_ok=True)


# ─── CSV thread-safe ──────────────────────────────────────────────────────────


class CsvWriter:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with open(self.path, "w", newline="") as f:
                csv.writer(f).writerow(["fecha", "pmm_imerg", "n_pixels"])

    def write_row(self, row: tuple):
        with self.lock:
            with open(self.path, "a", newline="") as f:
                csv.writer(f).writerow(row)

    def existing_dates(self) -> set[str]:
        dates = set()
        if self.path.exists():
            with open(self.path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dates.add(row["fecha"])
        return dates


# ─── Worker ───────────────────────────────────────────────────────────────────


def process_day(args: tuple) -> tuple[str, float, int] | None:
    date_str, url, token, tmp_dir = args
    return download_and_extract(date_str, url, token, tmp_dir)


# ─── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="ETL GPM_3IMERGDL → CSV diario valle")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--out", default="data/imerg/imerg_valle_daily.csv")
    args = parser.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end = datetime.strptime(args.end, "%Y-%m-%d").date()
    token = load_token()
    out_path = Path(args.out)
    writer = CsvWriter(out_path)
    existing = writer.existing_dates()
    log.info(
        f"Rango: {start} → {end} | Ya en CSV: {len(existing)} fechas | Workers: {args.workers}"
    )

    # Fase 1: CMR por mes
    log.info("Fase 1: consulta CMR por mes")
    all_granules: list[dict] = []
    d = start
    while d <= end:
        granules = query_cmr_month(token, d.year, d.month)
        # Filtrar por rango
        granules = [g for g in granules if start <= g["date"] <= end]
        all_granules.extend(granules)
        log.info(f"  {d.year}-{d.month:02d}: {len(granules)} granules")
        d = (date(d.year, d.month, 1) + timedelta(days=32)).replace(day=1)
        time.sleep(1)  # rate limit CMR

    # Filtrar ya existentes
    pending = [g for g in all_granules if g["date"].isoformat() not in existing]
    log.info(f"Total granules: {len(all_granules)} | Pendientes: {len(pending)}")

    if not pending:
        log.info("Nada que hacer. ✅")
        return

    # Fase 2: Descarga + extracción paralela
    log.info(f"Fase 2: descarga + extracción ({len(pending)} días, {args.workers} workers)")
    tmp_dir = Path(tempfile.mkdtemp(prefix="imerg_etl_"))

    done = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(process_day, (g["date"].isoformat(), g["url"], token, tmp_dir)): g["date"]
            for g in pending
        }
        for fut in as_completed(futures):
            day = futures[fut]
            try:
                result = fut.result()
                if result:
                    writer.write_row(result)
                    done += 1
                    if done % 50 == 0:
                        log.info(f"  Progreso: {done}/{len(pending)}")
                else:
                    failed += 1
            except Exception as e:
                log.warning(f"  Error {day}: {e}")
                failed += 1

    shutil.rmtree(tmp_dir, ignore_errors=True)
    log.info(f"Completado: {done} OK, {failed} fail. Total en CSV: {len(writer.existing_dates())}")


if __name__ == "__main__":
    main()
