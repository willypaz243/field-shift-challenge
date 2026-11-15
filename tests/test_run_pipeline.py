"""Tests for the model pipeline data loading (run_pipeline.load_history)."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model.run_pipeline import load_history  # noqa: E402

ROWS = [
    # IMERG present: it must win over POWER pmm
    ("D1_tunari", "2016-01-01", 8.0, 22.0, 15.0, 1.0, 3.5),
    # IMERG zero is a valid measurement (not a fallback case)
    ("D1_tunari", "2016-01-02", 9.0, 23.0, 16.0, 0.5, 0.0),
    # POWER-only day (IMERG NULL)
    ("D1_tunari", "2016-01-03", 7.0, 21.0, 14.0, 2.0, None),
    # IMERG outlier (>100 mm/day) must fall back to POWER
    ("D1_tunari", "2016-01-04", 7.5, 21.5, 14.5, 2.2, 999.0),
    # Other zone: must be filtered out
    ("D2_other", "2016-01-01", 8.0, 22.0, 15.0, 9.0, 9.0),
]


def make_db(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE climate_history (
            zone_id TEXT, fecha TEXT,
            tmin REAL, tmax REAL, tmean REAL, pmm REAL, rh REAL, sw REAL, ws REAL,
            et0 REAL, sm_surface REAL, sm_root REAL, pmm_sat REAL,
            PRIMARY KEY (zone_id, fecha)
        );
        """
    )
    con.executemany(
        "INSERT INTO climate_history (zone_id, fecha, tmin, tmax, tmean, pmm, "
        "rh, sw, ws, et0, sm_surface, sm_root, pmm_sat) "
        "VALUES (?, ?, ?, ?, ?, ?, 60, 20, 2.0, 4.0, NULL, NULL, ?)",
        [(z, f, mn, mx, tm, pw, sat) for z, f, mn, mx, tm, pw, sat in ROWS],
    )
    con.commit()
    con.close()


class LoadHistoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "t.db"
        make_db(self.db)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_filters_by_zone_and_date_range(self) -> None:
        series = load_history(self.db, "D1_tunari", "2016-01-01", "2016-01-02")
        self.assertEqual(series.dates, ["2016-01-01", "2016-01-02"])
        self.assertEqual(len(series.fields["tmean"]), 2)

    def test_imerg_primary_power_fallback(self) -> None:
        series = load_history(self.db, "D1_tunari", "2016-01-01", "2016-01-04")
        self.assertEqual([float(x) for x in series.fields["pmm"]], [3.5, 0.0, 2.0, 2.2])

    def test_other_variables_untouched(self) -> None:
        series = load_history(self.db, "D1_tunari", "2016-01-01", "2016-01-04")
        self.assertEqual([float(x) for x in series.fields["tmin"]], [8.0, 9.0, 7.0, 7.5])


if __name__ == "__main__":
    unittest.main()
