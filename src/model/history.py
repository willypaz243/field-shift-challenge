"""Consolidated climate history: one zone, daily, from valle.db.

`pmm` uses IMERG (`pmm_sat`) as the primary source (the 0.5 deg POWER cell
underestimates Andean convective rain) with POWER `pmm` as fallback; values
above 100 mm/day are treated as data errors (NaN).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

VARIABLES = ["tmean", "tmin", "tmax", "pmm"]


@dataclass
class HistorySeries:
    """Daily climate series for one zone over a date range."""

    dates: list[str]
    fields: dict[str, np.ndarray] = field(default_factory=dict)

    @property
    def n_days(self) -> int:
        return len(self.dates)


def load_history(db: Path, zone_id: str, start: str, end: str) -> HistorySeries:
    """Read `climate_history` from the consolidated DB for one zone."""
    con = sqlite3.connect(db)
    try:
        rows = con.execute(
            "SELECT fecha, tmean, tmin, tmax, pmm, pmm_sat FROM climate_history "
            "WHERE zone_id = ? AND fecha >= ? AND fecha <= ? ORDER BY fecha",
            (zone_id, start, end),
        ).fetchall()
    finally:
        con.close()
    dates: list[str] = []
    cols: dict[str, list] = {v: [] for v in VARIABLES}
    for fecha, tmean, tmin, tmax, pmm, pmm_sat in rows:
        dates.append(fecha)
        cols["tmean"].append(tmean)
        cols["tmin"].append(tmin)
        cols["tmax"].append(tmax)
        sat = pmm_sat if (pmm_sat is not None and pmm_sat <= 100) else None
        cols["pmm"].append(sat if sat is not None else pmm)
    fields: dict[str, np.ndarray] = {}
    for v in VARIABLES:
        arr = np.array([None if x is None else float(x) for x in cols[v]], dtype=float)
        if v == "pmm":
            arr[arr > 100] = np.nan
        fields[v] = arr
    return HistorySeries(dates=dates, fields=fields)
