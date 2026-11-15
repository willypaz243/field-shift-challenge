"""Pruebas con lluvia SINTÉTICA. Ningún valor constituye una observación NASA."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import xarray as xr
import imerg


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.area = self.root / "area.geojson"
        # Cruza dos celdas; ambos centros caen fuera del polígono.
        self.area.write_text(json.dumps({"type": "Polygon", "coordinates": [[
            [-66.21, -17.49], [-66.19, -17.49], [-66.19, -17.41],
            [-66.21, -17.41], [-66.21, -17.49]]]}))
        self.db = self.root / "rain.sqlite"

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, run="final", values=(0, np.nan), count=(48, 30), units="mm/day"):
        folder = self.root / run
        folder.mkdir(exist_ok=True)
        marker = "3B-DAY-L" if run == "late" else "3B-DAY"
        name = f"{marker}.MS.MRG.3IMERG.20250101-S000000-E235959.V07B.nc4"
        ds = xr.Dataset({
            "precipitation": (("time", "lat", "lon"), np.array(values).reshape(1, 1, 2), {"units": units}),
            "precipitation_cnt": (("time", "lat", "lon"), np.array(count).reshape(1, 1, 2), {"units": "count"})},
            coords={"time": [np.datetime64("2025-01-01")], "lat": [-17.45], "lon": [-66.25, -66.15]})
        ds.to_netcdf(folder / name)
        return folder

    def test_intersection_quality_zero_missing_and_idempotence(self):
        folder = self.fixture()
        for _ in range(2):
            imerg.process(folder, self.area, self.db, "final")
        con = imerg.open_db(self.db)
        rows = con.execute("SELECT value,quality,area_fraction FROM rain ORDER BY lon").fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], 0)
        self.assertIsNone(rows[1][0])
        self.assertEqual(json.loads(rows[1][1])["precipitation_cnt"]["value"], 30)
        self.assertAlmostEqual(rows[0][2], .08)
        con.close()
        out = self.root / "report.json"
        imerg.report(self.db, "2025-01-01", "2025-01-02", out)
        report = json.loads(out.read_text())
        self.assertEqual(len(report["missing_records"]), 2)
        self.assertEqual(report["null_values"], 1)

    def test_final_precedence_and_null_fallback(self):
        imerg.process(self.fixture("late", (10, 20)), self.area, self.db, "late")
        imerg.process(self.fixture("final", (5, np.nan)), self.area, self.db, "final")
        con = imerg.open_db(self.db)
        rows = con.execute("SELECT run,value FROM preferred_rain ORDER BY lon").fetchall()
        self.assertEqual(rows, [("final", 5), ("late", 20)])
        self.assertEqual(con.execute("SELECT count(*) FROM rain").fetchone()[0], 4)
        con.close()

    def test_wrong_units_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unidad inesperada"):
            imerg.process(self.fixture(units="mm/hr"), self.area, self.db, "final")

    def test_no_polygon_substitution(self):
        self.area.write_text('{"type":"Point","coordinates":[-66,-17]}')
        with self.assertRaisesRegex(ValueError, "polígono"):
            imerg.read_area(self.area)

    def test_update_twice_does_not_duplicate(self):
        self.fixture("late", (1, 2))
        self.fixture("final", (3, 4))
        entry = {"id": "test", "producer_granule_id": "synthetic.nc4",
                 "time_start": "2025-01-01T00:00:00Z", "updated": "test",
                 "links": [{"rel": "https://example.org/data#", "href": "https://example.org/synthetic.nc4"}]}
        with patch.object(imerg, "catalog", return_value=[entry]), patch.object(imerg, "download"):
            for _ in range(2):
                imerg.update(self.root, self.area, self.db)
        con = imerg.open_db(self.db)
        self.assertEqual(con.execute("SELECT count(*) FROM rain").fetchone()[0], 4)
        con.close()


if __name__ == "__main__":
    unittest.main()
