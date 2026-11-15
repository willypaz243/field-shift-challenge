"""Load the pipeline forecast into the forecasts table (issue #29 A4).

Reads the CSV written by `src.model.run_pipeline`
(data/model/forecast_valle.csv) and reloads `forecasts` for every zone.
The projection is valley-wide in this cut: the contract (§2.3) repeats
the same values in all zones. Idempotent: each load replaces the table
in one transaction and appends a `sync_version` row so clients
delta-sync. `rh`/`sw`/`ws`/`sm_surface`/`sm_root` stay NULL until the
climatology feed lands (issue #80 [T15]).

Usage:
    uv run python -m api.modules.climate.loader \
        --csv data/model/forecast_valle.csv \
        --db data/db/valle.db
"""

from __future__ import annotations

import argparse
import csv
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import delete
from sqlmodel import Session, select

from api.core.db import make_engine
from api.core.models import SyncVersion
from api.modules.climate.models import Forecast
from api.modules.zones.models import Zone

EXPECTED_COLUMNS = (
    "fecha",
    "tmean",
    "tmin",
    "tmax",
    "pmm",
    "et0",
    "tmean_baja",
    "tmean_alta",
    "tmin_baja",
    "tmin_alta",
    "pmm_baja",
    "pmm_alta",
    "et0_baja",
    "et0_alta",
)


def _float_or_none(raw: str | None) -> float | None:
    return None if raw is None else float(raw)


def _cell(raw: Any) -> str | None:
    """CSV cell: an empty string means a missing value."""
    if isinstance(raw, str) and raw:
        return raw
    return None


def _read_csv(csv_path: Path) -> list[dict[str, str | None]]:
    """Read the pipeline CSV, validating its header."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in EXPECTED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"forecast CSV is missing columns: {missing}")
        rows = [{c: _cell(row.get(c)) for c in EXPECTED_COLUMNS} for row in reader]
    if not rows:
        raise ValueError(f"forecast CSV has no rows: {csv_path}")
    return rows


def _rows_for_zone(
    zone_id: str, rows: list[dict[str, str | None]], created: datetime
) -> list[Forecast]:
    out = []
    for row in rows:
        fecha = date.fromisoformat(row["fecha"] or "")
        out.append(
            Forecast(
                zone_id=zone_id,
                fecha=fecha,
                anio=fecha.year,
                tmean=_float_or_none(row["tmean"]),
                tmin=_float_or_none(row["tmin"]),
                tmax=_float_or_none(row["tmax"]),
                pmm=_float_or_none(row["pmm"]),
                et0=_float_or_none(row["et0"]),
                tmin_min=_float_or_none(row["tmin_baja"]),
                tmin_max=_float_or_none(row["tmin_alta"]),
                pmm_min=_float_or_none(row["pmm_baja"]),
                pmm_max=_float_or_none(row["pmm_alta"]),
                creado_en=created,
            )
        )
    return out


def load_forecasts(csv_path: Path, db: Path) -> dict[str, Any]:
    """Replace `forecasts` from the pipeline CSV and bump the sync version."""
    rows = _read_csv(csv_path)
    created = datetime.now(UTC)
    engine = make_engine(f"sqlite:///{db}")
    try:
        with Session(engine) as session:
            zones = list(session.exec(select(Zone)).all())
            if not zones:
                raise ValueError(f"no zones in the database: {db}")
            session.exec(delete(Forecast))
            for zone in zones:
                session.add_all(_rows_for_zone(zone.id, rows, created))
            session.add(SyncVersion(creado_en=created, hash=""))
            session.commit()
            loaded = {"zones": len(zones), "days": len(rows), "rows": len(zones) * len(rows)}
    finally:
        engine.dispose()
    return {**loaded, "creado_en": created.isoformat()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/model/forecast_valle.csv")
    ap.add_argument("--db", default="data/db/valle.db")
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[3]
    result = load_forecasts(root / args.csv, root / args.db)
    print(
        f"Loaded {result['rows']} forecast rows ({result['zones']} zones x {result['days']} days), "
        f"creado_en {result['creado_en']}"
    )


if __name__ == "__main__":
    main()
