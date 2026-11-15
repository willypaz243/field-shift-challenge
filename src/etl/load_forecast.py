"""Load the valley forecast (`data/model/forecast_valle.csv`) into `forecasts`.

The model produces one series for the whole valley, so every zone gets the same
days; the `_baja`/`_alta` bands become `*_min`/`*_max` for the API uncertainty.
The table is replaced in full so a regenerated window does not leave stale days,
and a new `sync_version` row makes phones pull the new forecast.

Usage (weekly, after `src.model.run_pipeline`):
    uv run python -m src.etl.load_forecast --db data/db/valle.db
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import Engine

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.core.db import init_db, make_engine  # noqa: E402

COLUMNS = {
    "tmin": "tmin",
    "tmax": "tmax",
    "tmean": "tmean",
    "pmm": "pmm",
    "et0": "et0",
    "tmin_min": "tmin_baja",
    "tmin_max": "tmin_alta",
    "pmm_min": "pmm_baja",
    "pmm_max": "pmm_alta",
}


def _num(value: str | None) -> float | None:
    value = (value or "").strip()
    return float(value) if value else None


def load(engine: Engine, csv_path: Path) -> int:
    init_db(engine)
    with csv_path.open(newline="") as fh:
        days = list(csv.DictReader(fh))
    now = datetime.now(UTC).isoformat(timespec="seconds")
    raw = engine.raw_connection()
    try:
        con = raw.driver_connection
        assert con is not None
        zones = [z for (z,) in con.execute("SELECT id FROM zones ORDER BY id")]
        rows = [
            {
                "zone_id": zone,
                "fecha": d["fecha"],
                "anio": int(d["fecha"][:4]),
                "creado_en": now,
                **{col: _num(d.get(src)) for col, src in COLUMNS.items()},
            }
            for zone in zones
            for d in days
        ]
        with con:
            con.execute("DELETE FROM forecasts")
            if rows:
                cols = list(rows[0])
                con.executemany(
                    f"INSERT INTO forecasts ({', '.join(cols)}) "
                    f"VALUES ({', '.join(':' + c for c in cols)})",
                    rows,
                )
            con.execute("INSERT INTO sync_version (creado_en, hash) VALUES (?, ?)", (now, ""))
    finally:
        raw.close()
    return len(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "data" / "db" / "valle.db"))
    ap.add_argument("--csv", default=str(ROOT / "data" / "model" / "forecast_valle.csv"))
    args = ap.parse_args()
    count = load(make_engine(f"sqlite:///{args.db}"), Path(args.csv))
    print(f"forecasts: {count} rows")


if __name__ == "__main__":
    main()
