"""Training and metrics report plots.

Renders the model's progress as PNG charts: history vs fit, backtest
holdout (observed vs predicted), MAE/RMSE per variable, and the forecast
with its uncertainty bands.

Usage:
    .venv/bin/python -m src.model.plot_report \
        --db data/db/valle.db --zone D1_tunari \
        --horizon 365 --today 2026-11-15 --out docs/plots
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .backtest import Backtester  # noqa: E402
from .forecast import ForecastBuilder, ForecastResult  # noqa: E402
from .history import VARIABLES, HistorySeries, load_history  # noqa: E402
from .seasonal import backtest as bt_metrics  # noqa: E402
from .seasonal import fit, predict  # noqa: E402

UNITS = {"tmean": "°C", "tmin": "°C", "tmax": "°C", "pmm": "mm"}
HOLDOUT_START = "2024-01-01"
BACKTEST_HORIZON = 731


def plot_training_fit(series: HistorySeries, out: Path) -> None:
    t = np.arange(series.n_days, dtype=float)
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    for ax, v in zip(axes.ravel(), VARIABLES, strict=False):
        y = series.fields[v]
        m = ~np.isnan(y)
        ax.scatter(t[m], y[m], s=1, alpha=0.4, label="history")
        f = fit(y[m], t[m])
        ax.plot(t, predict(f, t), color="tab:red", lw=1.5, label="fit")
        ax.set_title(f"{v} ({UNITS[v]})")
        ax.grid(alpha=0.3)
    axes[-1, 0].set_xlabel("day (from the series start)")
    fig.suptitle(f"Training: {series.dates[0]} → {series.dates[-1]}")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_backtest(series: HistorySeries, out: Path) -> None:
    dates = series.dates
    i_hold = next(i for i, d in enumerate(dates) if d == HOLDOUT_START)
    t = np.arange(series.n_days, dtype=float)
    t_hold = float(t[i_hold])
    i1 = min(series.n_days - 1, i_hold + BACKTEST_HORIZON)
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    for ax, v in zip(axes.ravel(), VARIABLES, strict=False):
        y = series.fields[v]
        m = ~np.isnan(y)
        ym, tm = y[m], t[m]
        tr = tm < t_hold
        f = fit(ym[tr], tm[tr])
        t_test = np.arange(t_hold, t_hold + BACKTEST_HORIZON, dtype=float)
        pred = predict(f, t_test)
        ax.plot(t[i_hold : i1 + 1], y[i_hold : i1 + 1], color="tab:blue", lw=1.0, label="observed")
        ax.plot(t_test, pred, color="tab:red", lw=1.5, label="predicted")
        mae, rmse = bt_metrics(y, t, t_hold, BACKTEST_HORIZON)
        ax.set_title(f"{v} — MAE {mae:.2f} / RMSE {rmse:.2f} ({UNITS[v]})")
        ax.grid(alpha=0.3)
        ax.legend()
    axes[-1, 0].set_xlabel("day (from the series start)")
    fig.suptitle(f"Backtest holdout {HOLDOUT_START} → +{BACKTEST_HORIZON} d")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_metrics(metrics: list[dict[str, Any]], out: Path) -> None:
    names = [m["variable"] for m in metrics]
    mae = [m["mae"] for m in metrics]
    rmse = [m["rmse"] for m in metrics]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - 0.2, mae, width=0.4, label="MAE", color="tab:blue")
    ax.bar(x + 0.2, rmse, width=0.4, label="RMSE", color="tab:red")
    for xi, (a, b) in enumerate(zip(mae, rmse, strict=False)):
        ax.text(xi - 0.2, a, f"{a:.2f}", ha="center", va="bottom", fontsize=8)
        ax.text(xi + 0.2, b, f"{b:.2f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x, names)
    ax.set_ylabel("error")
    ax.set_title(f"Backtest {HOLDOUT_START} → +{BACKTEST_HORIZON} d (MAE / RMSE)")
    ax.grid(alpha=0.3, axis="y")
    ax.legend()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_forecast(result: ForecastResult, out: Path) -> None:
    h = np.arange(1, len(result.dates) + 1, dtype=float)
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    for ax, v in zip(axes.ravel(), VARIABLES, strict=False):
        mean = result.fields[v]
        band = result.bands[v]
        ax.plot(h, mean, color="tab:blue", lw=1.5, label="mean")
        ax.fill_between(h, mean - band, mean + band, alpha=0.3, label="± band")
        ax.set_title(f"{v} ({UNITS[v]})")
        ax.grid(alpha=0.3)
    axes[0, 0].legend()
    axes[-1, 0].set_xlabel("day from today")
    fig.suptitle(f"Forecast {result.dates[0]} → {result.dates[-1]}")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/db/valle.db")
    ap.add_argument("--zone", default="D1_tunari")
    ap.add_argument("--start", default="2016-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--horizon", type=int, default=365)
    ap.add_argument("--today", default=None, help="ISO date; default = system date")
    ap.add_argument("--out", default="docs/plots")
    a = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    series = load_history(root / a.db, a.zone, a.start, a.end)
    out = root / a.out
    out.mkdir(parents=True, exist_ok=True)

    plot_training_fit(series, out / "training_fit.png")
    plot_backtest(series, out / "backtest_holdout.png")
    metrics = Backtester(series, BACKTEST_HORIZON).metrics(HOLDOUT_START)
    plot_metrics(metrics, out / "metrics_summary.png")
    today = date.fromisoformat(a.today) if a.today else date.today()
    result = ForecastBuilder(series, a.horizon, today).build()
    plot_forecast(result, out / "forecast_bands.png")
    print(f"Plots written to {out}")


if __name__ == "__main__":
    main()
