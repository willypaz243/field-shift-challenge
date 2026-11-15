"""Tests for the seasonal model design matrix and trend handling."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model.seasonal import N_HARMONICS, _design, fit, predict  # noqa: E402


class DesignMatrixTest(unittest.TestCase):
    def test_shape_and_full_rank(self) -> None:
        t = np.arange(100, dtype=float)
        X = _design(t)
        self.assertEqual(X.shape, (100, 2 + 2 * N_HARMONICS))
        self.assertEqual(np.linalg.matrix_rank(X), X.shape[1])

    def test_columns_intercept_trend_harmonics(self) -> None:
        t = np.arange(50, dtype=float)
        X = _design(t)
        self.assertTrue((X[:, 0] == 1).all())
        self.assertTrue((X[:, 1] == t).all())


class TrendFitTest(unittest.TestCase):
    def test_fit_recovers_linear_trend(self) -> None:
        # A pure linear signal must be reproduced exactly by the fit.
        t = np.arange(0, 730, dtype=float)
        slope = 0.01
        y = 10.0 + slope * t
        f = fit(y, t)
        pred = predict(f, t)
        self.assertLess(float(np.max(np.abs(pred - y))), 1e-6)


if __name__ == "__main__":
    unittest.main()
