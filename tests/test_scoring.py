"""Tests for the window scoring reference function (task 12a, issue #37).

Runs the published test vectors (data/model/test_vectors.json) that the
mobile app must reproduce, plus the verdict mapping with configurable
thresholds.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model.scoring import (  # noqa: E402
    VERDICT_GOOD,
    VERDICT_POOR,
    score_window,
    veredicto,
)

ROOT = Path(__file__).resolve().parents[1]
VECTORS = json.loads((ROOT / "data" / "model" / "test_vectors.json").read_text())["vectores"]


def run_vector(v: dict[str, Any]) -> dict[str, Any]:
    e = v["entrada"]
    return score_window(
        e["cultivo"],
        e["zona"],
        e["tmean"],
        e["tmin"],
        e["pmm"],
        e["et0"],
        horizon=e.get("horizon"),
        pos=e.get("pos", 0),
    )


class TestVectorsTest(unittest.TestCase):
    """The published vectors are the portability contract for the mobile app."""

    def test_at_least_ten_vectors(self) -> None:
        self.assertGreaterEqual(len(VECTORS), 10)

    def test_all_vectors_match_expected_output(self) -> None:
        for v in VECTORS:
            with self.subTest(id=v["id"]):
                out = run_vector(v)
                expected = v["esperado"]
                self.assertEqual(out["score"], expected["score"])
                self.assertEqual(out["veredicto"], expected["veredicto"])
                self.assertEqual(out["confianza"], expected["confianza"])
                self.assertEqual(out["motivos"], expected["motivos"])
                self.assertEqual(out["detalle"], expected["detalle"])

    def test_motivo_order_is_stable(self) -> None:
        # Codes are always emitted in the documented order.
        for v in VECTORS:
            with self.subTest(id=v["id"]):
                out = run_vector(v)
                order = ["temp_fuera_rango", "deficit_agua", "heladas", "erosion_riesgo"]
                self.assertEqual(out["motivos"], [m for m in order if m in out["motivos"]])


class VeredictoTest(unittest.TestCase):
    def test_default_boundaries(self) -> None:
        self.assertEqual(veredicto(100.0), "bueno")
        self.assertEqual(veredicto(VERDICT_GOOD), "bueno")
        self.assertEqual(veredicto(69.9), "con_cuidado")
        self.assertEqual(veredicto(VERDICT_POOR), "con_cuidado")
        self.assertEqual(veredicto(39.9), "malo")
        self.assertEqual(veredicto(0.0), "malo")

    def test_configurable_thresholds(self) -> None:
        self.assertEqual(veredicto(80.0, umbral_bueno=80, umbral_malo=30), "bueno")
        self.assertEqual(veredicto(79.9, umbral_bueno=80, umbral_malo=30), "con_cuidado")
        self.assertEqual(veredicto(30.0, umbral_bueno=80, umbral_malo=30), "con_cuidado")
        self.assertEqual(veredicto(29.9, umbral_bueno=80, umbral_malo=30), "malo")

    def test_score_window_uses_configurable_thresholds(self) -> None:
        v = next(v for v in VECTORS if v["id"] == "v04_deficit_agua_severo")
        # Score is 60.0: con_cuidado by default, bueno with umbral_bueno=60.
        e = v["entrada"]
        out = score_window(e["cultivo"], e["zona"], e["tmean"], e["tmin"], e["pmm"], e["et0"])
        self.assertEqual(out["veredicto"], "con_cuidado")
        out = score_window(
            e["cultivo"],
            e["zona"],
            e["tmean"],
            e["tmin"],
            e["pmm"],
            e["et0"],
            umbral_bueno=60.0,
        )
        self.assertEqual(out["veredicto"], "bueno")


if __name__ == "__main__":
    unittest.main()
