#!/usr/bin/env python3
"""
ETL GPM_3IMERGDL v07 — daily valley precipitation (Cochabamba).

- Queries CMR by month (concept-id=C2723754859-GES_DISC).
- Downloads global NetCDF4 granules (~1/day, ~27 MB each).
- Extracts `precipitation` (mm/day) -> daily mean over the valley pixels.
- Output CSV: fecha, pmm_imerg, n_pixels
- Resumable: skips dates already present in the CSV.
- Parallel pipeline: threaded downloads (keep-alive sessions, retries) piped
  into process-based extraction (the HDF5 library is not thread-safe; one
  process per file removes the need for a global lock).

Usage:
    .venv/bin/python src/etl/imerg_etl.py --start 2016-01-01 --end 2025-12-31 \
        --workers 8 --extract-workers 4 --out data/imerg/imerg_valle_daily.csv
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import re
import shutil
import tempfile
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import requests

# ─── Config ───────────────────────────────────────────────────────────────────

CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"
COLLECTION_ID = "C2723754859-GES_DISC"  # GPM_3IMERGDL v07

# BBOX of the valley of Cochabamba (WGS84)
BBOX = {
    "west": -66.40,
    "south": -17.65,
    "east": -65.95,
    "north": -17.15,
}

DOWNLOAD_ATTEMPTS = 3

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
    """Return a list of {date, url} for a month."""
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    params = {
        "concept-id": COLLECTION_ID,
        "temporal": f"{start.isoformat()}T00:00:00Z,{end.isoformat()}T00:00:00Z",
        "bounding_box": f"{BBOX['west']},{BBOX['south']},{BBOX['east']},{BBOX['north']}",
        "provider": "GES_DISC",
        "page_size": "500",  # CMR no longer uses `limit`; default = 10 granules
    }
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    resp = requests.get(CMR_URL, params=params, headers=headers, timeout=60)
    resp.raise_for_status()
    entries = resp.json().get("feed", {}).get("entry", [])

    results = []
    for e in entries:
        title = e.get("producer_granule_id", "") or e.get("title", "")
        # Format: 3B-DAY-L.MS.MRG.3IMERG.20251101-S000000-E235959.V07B
        m = re.search(r"3IMERG\.(\d{8})-S", title)
        if not m:
            continue
        granule_date = datetime.strptime(m.group(1), "%Y%m%d").date()
        if not (start <= granule_date < end):
            continue
        url = None
        for link in e.get("links", []):
            if link.get("rel", "").endswith("data#"):
                url = link["href"]
                break
        if url:
            results.append({"date": granule_date, "url": url})

    return results


# ─── Download (threads) ───────────────────────────────────────────────────────

_tls = threading.local()


def http_session(token: str) -> requests.Session:
    """One keep-alive session per thread: skips the TLS handshake per file."""
    s = getattr(_tls, "session", None)
    if s is None:
        s = requests.Session()
        if token:
            s.headers["Authorization"] = f"Bearer {token}"
        _tls.session = s
    return s


def download_granule(date_str: str, url: str, token: str, tmp_dir: Path) -> Path | None:
    """Download one granule with retries. Returns the local path or None."""
    filepath = tmp_dir / f"imerg_{date_str}.nc4"
    session = http_session(token)
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            with session.get(url, stream=True, timeout=300) as r:
                r.raise_for_status()
                # GES DISC can drop the connection mid-body without an HTTP
                # error: validate the byte count against Content-Length.
                expected = int(r.headers.get("Content-Length") or 0)
                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(chunk_size=256 * 1024):
                        f.write(chunk)
            actual = filepath.stat().st_size
            if expected and actual != expected:
                raise OSError(f"incomplete download: {actual}/{expected} bytes")
            return filepath
        except Exception as e:
            log.warning(f"download {date_str} attempt {attempt}: {e}")
            filepath.unlink(missing_ok=True)
            if attempt < DOWNLOAD_ATTEMPTS:
                time.sleep(2 * attempt)
    return None


# ─── Extraction (processes) ───────────────────────────────────────────────────


def extract_valley(filepath: Path, date_str: str) -> tuple[str, float, int] | None:
    """Extract daily valley precipitation. Runs in a worker process: each
    process owns its HDF5 library instance, so no shared lock is needed."""
    import netCDF4

    try:
        ds = netCDF4.Dataset(str(filepath), "r")
        # Real shape: (time=1, lon=3600, lat=1800) — already daily total (mm)
        precip = ds.variables["precipitation"][:]
        lats = ds.variables["lat"][:]
        lons = ds.variables["lon"][:]
        ds.close()

        # Valley mask: (lon, lat)
        lon_mask = (lons >= BBOX["west"]) & (lons <= BBOX["east"])
        lat_mask = (lats >= BBOX["south"]) & (lats <= BBOX["north"])
        pixel_mask = np.outer(lon_mask, lat_mask)  # (lon=3600, lat=1800)

        n_pixels = int(pixel_mask.sum())
        if n_pixels == 0:
            log.warning(f"{date_str}: 0 pixels in bbox")
            return None

        # Take the single day (time=0) -> (lon, lat)
        daily = precip[0]
        valley_pixels = daily[pixel_mask]
        # Filter invalid values (NetCDF fill = -9999 or NaN)
        valid = valley_pixels[~np.isnan(valley_pixels) & (valley_pixels > -9000)]
        if len(valid) == 0:
            return None
        return (date_str, float(valid.mean()), n_pixels)

    except Exception as e:
        log.warning(f"extract {date_str}: {e}")
        return None
    finally:
        filepath.unlink(missing_ok=True)


# ─── CSV ──────────────────────────────────────────────────────────────────────


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
                for row in csv.DictReader(f):
                    dates.add(row["fecha"])
        return dates


def finalize_csv(path: Path) -> int:
    """Rewrite the CSV sorted by date, keeping the first row of any duplicate."""
    rows: dict[str, dict] = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.setdefault(r["fecha"], r)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fecha", "pmm_imerg", "n_pixels"])
        for k in sorted(rows):
            w.writerow([k, rows[k]["pmm_imerg"], rows[k]["n_pixels"]])
    return len(rows)


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="ETL GPM_3IMERGDL -> daily valley CSV")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--workers", type=int, default=8, help="parallel downloads")
    parser.add_argument("--extract-workers", type=int, default=4, help="parallel extractions")
    parser.add_argument("--out", default="data/imerg/imerg_valle_daily.csv")
    args = parser.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end = datetime.strptime(args.end, "%Y-%m-%d").date()
    token = load_token()
    out_path = Path(args.out)
    writer = CsvWriter(out_path)
    existing = writer.existing_dates()
    log.info(
        f"Range: {start} -> {end} | Already in CSV: {len(existing)} dates | Workers: {args.workers}"
    )

    # Phase 1: CMR by month
    log.info("Phase 1: CMR query by month")
    all_granules: list[dict] = []
    d = start
    while d <= end:
        granules = query_cmr_month(token, d.year, d.month)
        granules = [g for g in granules if start <= g["date"] <= end]
        all_granules.extend(granules)
        log.info(f"  {d.year}-{d.month:02d}: {len(granules)} granules")
        d = (date(d.year, d.month, 1) + timedelta(days=32)).replace(day=1)
        time.sleep(1)  # CMR rate limit

    pending = [g for g in all_granules if g["date"].isoformat() not in existing]
    log.info(f"Total granules: {len(all_granules)} | Pending: {len(pending)}")

    if not pending:
        log.info("Nothing to do.")
        return

    # Phase 2: downloads (threads) piped into extraction (processes)
    log.info(
        f"Phase 2: download + extract ({len(pending)} days, "
        f"{args.workers} dl / {args.extract_workers} ext workers)"
    )
    tmp_dir = Path(tempfile.mkdtemp(prefix="imerg_etl_"))

    done = 0
    failed = 0
    with (
        ThreadPoolExecutor(max_workers=args.workers) as dl,
        ProcessPoolExecutor(max_workers=args.extract_workers) as ex,
    ):
        extract_map: dict = {}
        dl_map = {
            dl.submit(download_granule, g["date"].isoformat(), g["url"], token, tmp_dir): g["date"]
            for g in pending
        }
        for fut in as_completed(dl_map):
            day = dl_map[fut]
            filepath = fut.result()
            if filepath is None:
                failed += 1
                continue
            date_str = day.isoformat()
            extract_map[ex.submit(extract_valley, filepath, date_str)] = date_str
        for ef in as_completed(extract_map):
            date_str = extract_map[ef]
            result = ef.result()
            if result:
                writer.write_row(result)
                done += 1
                if done % 50 == 0:
                    log.info(f"  Progress: {done}/{len(pending)}")
            else:
                failed += 1
                log.warning(f"  no data extracted for {date_str}")

    shutil.rmtree(tmp_dir, ignore_errors=True)
    total = finalize_csv(out_path)
    log.info(f"Done: {done} OK, {failed} failed. CSV total: {total} dates")


if __name__ == "__main__":
    main()
