"""Schema validation for data/crops/crops.json (issue #36, task T15)."""

import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CROPS_JSON = ROOT / "data" / "crops" / "crops.json"


def load_catalog() -> dict:
    return json.loads(CROPS_JSON.read_text())


class CatalogTest(unittest.TestCase):
    def test_version_and_updated_date(self):
        d = load_catalog()
        self.assertEqual(d["version"], 3)
        date.fromisoformat(d["actualizado"])

    def test_all_crops_have_kc_hail_stages_photo(self):
        d = load_catalog()
        for c in d["crops"]:
            with self.subTest(crop=c["id"]):
                kc = c.get("kc")
                self.assertIsInstance(kc, dict)
                for stage in ("inicial", "medio", "final"):
                    self.assertIsInstance(kc.get(stage), (int, float))
                self.assertIn(c.get("granizo_sens"), ("alta", "media", "baja"))
                self.assertIsInstance(c.get("etapas"), list)
                self.assertGreater(len(c["etapas"]), 0)
                self.assertIsInstance(c.get("foto"), str)

    STAGE_CODES = {"siembra", "crecimiento", "floracion", "granos", "cosecha"}

    def test_stages_monotonic_within_cycle(self):
        d = load_catalog()
        for c in d["crops"]:
            with self.subTest(crop=c["id"]):
                cycle = c.get("ciclo_dias")
                self.assertIsInstance(cycle, list)
                self.assertEqual(len(cycle), 2)
                stages = c["etapas"]
                for i, stage in enumerate(stages):
                    self.assertEqual(len(stage), 2)
                    day, code = stage
                    self.assertIsInstance(day, int)
                    self.assertGreaterEqual(day, 0)
                    self.assertLessEqual(day, cycle[1])
                    self.assertIn(code, self.STAGE_CODES)
                    if i > 0:
                        self.assertGreaterEqual(day, stages[i - 1][0])

    def test_perennials_have_harvest_interval(self):
        d = load_catalog()
        perennials = [c for c in d["crops"] if c.get("tipo_ciclo") == "perenne"]
        self.assertEqual(sorted(c["id"] for c in perennials), ["alfalfa", "durazno"])
        for c in perennials:
            with self.subTest(crop=c["id"]):
                interval = c.get("cosechas_cada_dias")
                self.assertIsInstance(interval, int)
                self.assertNotIsInstance(interval, bool)
                self.assertGreater(interval, 0)

    STANDARD_FIELDS = (
        "nombre",
        "cientifico",
        "tipo",
        "tipo_ciclo",
        "ciclo_dias",
        "temp",
        "helada",
        "agua",
        "altitud",
        "erosion_sens",
        "fix_n",
        "breaks_pest_cycle",
        "forage_value",
        "drought_tolerant",
        "deep_rooting",
        "kc",
        "granizo_sens",
        "etapas",
        "foto",
        "mercado",
        "siembra_local",
        "rotacion",
        "fuente",
    )

    def test_maiz_forraje_has_source(self):
        d = load_catalog()
        crop = next(c for c in d["crops"] if c["id"] == "maiz_forraje")
        for field in self.STANDARD_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, crop)
        self.assertTrue(crop["fuente"].strip())

    def test_photos_exist_in_mockups(self):
        d = load_catalog()
        for c in d["crops"]:
            with self.subTest(crop=c["id"]):
                photo = ROOT / "mockups" / c["foto"]
                self.assertTrue(photo.is_file())

    def test_id_equivalences_documented(self):
        readme = (ROOT / "data" / "crops" / "README.md").read_text()
        lines = [ln for ln in readme.splitlines() if "maiz" in ln.lower()]
        self.assertTrue(any("choclo" in ln.lower() for ln in lines))

    def test_fourteen_crops_with_unique_ids(self):
        d = load_catalog()
        ids = [c["id"] for c in d["crops"]]
        self.assertEqual(len(ids), 14)
        self.assertEqual(len(set(ids)), 14)
        self.assertIn("choclo", ids)
        self.assertIn("maiz_forraje", ids)
        self.assertNotIn("maiz", ids)


if __name__ == "__main__":
    unittest.main()
