import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TABLES = {
    "climate_history",
    "crops",
    "events",
    "feedback",
    "forecasts",
    "reports",
    "sync_version",
    "zones",
}


class DatabaseSchemaTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test.db"
        self.env = {
            **os.environ,
            "DATABASE_URL": f"sqlite:///{self.db_path}",
        }
        result = subprocess.run(
            [sys.executable, "-m", "api.db"],
            cwd=ROOT,
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def tearDown(self):
        self.tmp.cleanup()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def test_creates_the_eight_tables(self):
        with self.connect() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
        self.assertEqual(tables, EXPECTED_TABLES)

    def test_engine_enables_foreign_keys(self):
        code = (
            "from sqlalchemy import text\n"
            "from api.db import engine\n"
            "with engine.connect() as conn:\n"
            "    print(conn.execute(text('PRAGMA foreign_keys')).scalar())\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "1")

    def test_reports_idempotency_key_is_unique(self):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO zones (id, nombre, comuna, lat, lon, es_agricola, altitud_alta) "
                "VALUES ('D9_itocta', 'Itocta', 'ITOCTA', -17.46, -66.21, 1, 0)"
            )
            conn.execute(
                "INSERT INTO reports "
                "(idempotency_key, tipo, zone_id, lat, lon, ocurrido_en, creado_en) "
                "VALUES ('key-1', 'helada', 'D9_itocta', -17.46, -66.21, "
                "'2026-11-15 06:00:00', '2026-11-15 06:00:00')"
            )
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO reports "
                    "(idempotency_key, tipo, zone_id, lat, lon, ocurrido_en, creado_en) "
                    "VALUES ('key-1', 'helada', 'D9_itocta', -17.46, -66.21, "
                    "'2026-11-15 07:00:00', '2026-11-15 07:00:00')"
                )

    def test_climate_history_has_unique_zone_and_date(self):
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO zones (id, nombre, comuna, lat, lon, es_agricola, altitud_alta) "
                "VALUES ('D9_itocta', 'Itocta', 'ITOCTA', -17.46, -66.21, 1, 0)"
            )
            conn.execute(
                "INSERT INTO climate_history (zone_id, fecha, tmean) "
                "VALUES ('D9_itocta', '2026-01-01', 17.0)"
            )
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO climate_history (zone_id, fecha, tmean) "
                    "VALUES ('D9_itocta', '2026-01-01', 18.0)"
                )


if __name__ == "__main__":
    unittest.main()
