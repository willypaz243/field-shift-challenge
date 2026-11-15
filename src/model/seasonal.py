"""Time-series model: seasonality (Fourier, 4 harmonics) + linear trend.

- Least-squares fit (numpy, no external dependencies).
- N-day forecast with an uncertainty band that grows with the horizon:

      band(h) = 1.96 * sigma_residual * sqrt(1 + h/180)

  (sigma = residual standard deviation; at 180 days the band doubles).
- Backtest: 2024-2025 holdout -> MAE/RMSE per variable (task 2.3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

N_HARMONICS = 4
YEAR_DAYS = 365.25


def valid_mask(arr: np.ndarray) -> np.ndarray:
    return ~np.isnan(arr)


@dataclass
class Fit:
    coef: np.ndarray
    sigma: float
    t_start: float
    t_end: float
    n: int
    metrics: dict[str, Any] = field(default_factory=dict)


def _design(t: np.ndarray) -> np.ndarray:
    """Columns: intercept, linear trend, then cos/sin pairs (k=1..N_HARMONICS)."""
    X = np.ones((len(t), 2 + 2 * N_HARMONICS))
    X[:, 1] = t
    for k in range(1, N_HARMONICS + 1):
        X[:, 2 + 2 * (k - 1)] = np.cos(2 * np.pi * k * t / YEAR_DAYS)
        X[:, 2 + 2 * (k - 1) + 1] = np.sin(2 * np.pi * k * t / YEAR_DAYS)
    return X


def fit(y: np.ndarray, t: np.ndarray) -> Fit:
    """Fit Fourier(4) + linear trend to y (daily values). t = days since t0."""
    X = _design(t)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    sigma = float(np.std(resid, ddof=2))
    return Fit(coef=coef, sigma=sigma, t_start=float(t[0]), t_end=float(t[-1]), n=len(t))


def predict(fit: Fit, t: np.ndarray) -> np.ndarray:
    X = _design(t)
    return X @ fit.coef


def forecast(
    fit: Fit, horizon: int = 365, t_start: float | None = None
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Forecast `horizon` days from `t_start` (default: last data day).

    Returns (horizons, mean, band). The band grows with the horizon from t_start.
    """
    h = np.arange(1, horizon + 1, dtype=float)
    t0 = fit.t_end if t_start is None else t_start
    t = t0 + h
    mean = predict(fit, t)
    band = 1.96 * fit.sigma * np.sqrt(1.0 + h / 180.0)
    return h, mean, band


def backtest(
    y: np.ndarray,
    t: np.ndarray,
    holdout_start: float,
    horizon: int,
) -> tuple[float, float]:
    """MAE/RMSE forecasting `horizon` days from `holdout_start` (ignores NaN)."""
    m = ~np.isnan(y)
    y, t = y[m], t[m]
    mask_train = t < holdout_start
    fit_tr = fit(y[mask_train], t[mask_train])
    t_test = np.arange(holdout_start, holdout_start + horizon, dtype=float)
    pred = predict(fit_tr, t_test)
    actual = np.interp(t_test, t, y)
    err = pred - actual
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    return mae, rmse


def metrics_for(
    y: np.ndarray, t: np.ndarray, name: str, holdout: float, horizon: int
) -> dict[str, Any]:
    mae, rmse = backtest(y, t, holdout, horizon)
    return {"variable": name, "mae": round(mae, 3), "rmse": round(rmse, 3)}


class SeasonalModel:
    """Fitted seasonal model for one variable, with predict/forecast/backtest."""

    def __init__(self, y: np.ndarray, t: np.ndarray) -> None:
        self.fit: Fit = fit(y, t)

    def predict(self, t: np.ndarray) -> np.ndarray:
        return predict(self.fit, t)

    def forecast(
        self, horizon: int = 365, t_start: float | None = None
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        return forecast(self.fit, horizon, t_start)

    def backtest(
        self, y: np.ndarray, t: np.ndarray, holdout_start: float, horizon: int
    ) -> tuple[float, float]:
        return backtest(y, t, holdout_start, horizon)
