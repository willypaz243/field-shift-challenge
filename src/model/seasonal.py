"""Modelo de serie temporal: estacionalidad (Fourier, 4 armónicos) + tendencia lineal.

- Ajuste por mínimos cuadrados (numpy, sin dependencias externas).
- Proyección N días con banda de incertidumbre que crece con el horizonte:

      banda(h) = 1.96 · σ_residuo · √(1 + h/180)

  (σ = desviación de los residuos; a 180 días la banda se duplica).
- Backtest: holdout de 2024–2025 → MAE/RMSE por variable (tarea 2.3).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

N_HARMONICS = 4
YEAR_DAYS = 365.25


@dataclass
class Fit:
    coef: np.ndarray
    sigma: float
    t_start: float
    t_end: float
    n: int
    metrics: dict = field(default_factory=dict)


def _design(t: np.ndarray) -> np.ndarray:
    X = np.ones((len(t), 2 + 2 * N_HARMONICS))
    for k in range(1, N_HARMONICS + 1):
        X[:, 2 + 2 * (k - 1)] = np.cos(2 * np.pi * k * t / YEAR_DAYS)
        X[:, 2 + 2 * (k - 1) + 1] = np.sin(2 * np.pi * k * t / YEAR_DAYS)
    return X


def fit(y: np.ndarray, t: np.ndarray) -> Fit:
    """Ajusta Fourier(4) + tendencia a y (valores diarios). t = días desde t0."""
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
    """Proyecta `horizon` días desde `t_start` (por defecto, último día de datos).

    Devuelve (horizons, media, banda). La banda crece con el horizonte desde t_start.
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
    """MAE/RMSE proyectando `horizon` días desde `holdout_start` (ignora NaN)."""
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


def metrics_for(y: np.ndarray, t: np.ndarray, name: str, holdout: float, horizon: int) -> dict:
    mae, rmse = backtest(y, t, holdout, horizon)
    return {"variable": name, "mae": round(mae, 3), "rmse": round(rmse, 3)}
