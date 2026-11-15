"""Backtest: MAE/RMSE on a holdout period (2024-2025 by default)."""

from __future__ import annotations

from typing import Any

import numpy as np

from .history import VARIABLES, HistorySeries
from .seasonal import metrics_for


class Backtester:
    """Holds out the last days of the history and scores the fit against them."""

    def __init__(self, series: HistorySeries, horizon: int = 731) -> None:
        self.series = series
        self.horizon = horizon

    def metrics(self, holdout_start: str) -> list[dict[str, Any]]:
        dates = self.series.dates
        i_hold = next(i for i, d in enumerate(dates) if d == holdout_start)
        t = np.arange(len(dates), dtype=float)
        t_hold = float(t[i_hold])
        return [metrics_for(self.series.fields[v], t, v, t_hold, self.horizon) for v in VARIABLES]
