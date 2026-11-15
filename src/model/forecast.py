"""N-day forecast from the seasonal fits: mean per variable, uncertainty
bands that grow with the horizon, and ET0 (Hargreaves) derived from it."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from .et0 import et0_hargreaves
from .history import VARIABLES, HistorySeries
from .seasonal import fit, forecast, valid_mask


@dataclass
class ForecastResult:
    """Daily forecast arrays (index 0 = tomorrow) with uncertainty bands."""

    dates: list[str]
    fields: dict[str, np.ndarray]
    bands: dict[str, np.ndarray]
    et0: np.ndarray


class ForecastBuilder:
    """Fits the history per variable and projects `horizon` days from `today`."""

    def __init__(self, series: HistorySeries, horizon: int, today: date) -> None:
        self.series = series
        self.horizon = horizon
        self.today = today

    def build(self) -> ForecastResult:
        dates = self.series.dates
        data = self.series.fields
        t = np.arange(len(dates), dtype=float)
        t_today = (self.today - date.fromisoformat(dates[0])).days

        fits = {}
        for v in VARIABLES:
            m = valid_mask(data[v])
            fits[v] = fit(data[v][m], t[m])

        fdates = [(self.today + timedelta(days=i + 1)).isoformat() for i in range(self.horizon)]
        fields: dict[str, np.ndarray] = {}
        bands: dict[str, np.ndarray] = {}
        for v in VARIABLES:
            h, mean, band = forecast(fits[v], self.horizon, t_start=float(t_today))
            fields[v] = np.clip(mean, 0, None) if v == "pmm" else mean
            bands[v] = band

        doy = np.array(
            [(self.today + timedelta(days=i + 1)).timetuple().tm_yday for i in range(self.horizon)]
        )
        et0 = np.clip(et0_hargreaves(fields["tmean"], fields["tmax"], fields["tmin"], doy), 0, None)
        return ForecastResult(dates=fdates, fields=fields, bands=bands, et0=et0)


def write_forecast_csv(result: ForecastResult, out: Path) -> None:
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "fecha",
                "tmean",
                "tmin",
                "tmax",
                "pmm",
                "et0",
                "tmean_baja",
                "tmean_alta",
                "tmin_baja",
                "tmin_alta",
                "pmm_baja",
                "pmm_alta",
                "et0_baja",
                "et0_alta",
            ]
        )
        fields, bands, et0 = result.fields, result.bands, result.et0
        for i, fd in enumerate(result.dates):
            w.writerow(
                [
                    fd,
                    f"{fields['tmean'][i]:.2f}",
                    f"{fields['tmin'][i]:.2f}",
                    f"{fields['tmax'][i]:.2f}",
                    f"{fields['pmm'][i]:.2f}",
                    f"{et0[i]:.2f}",
                    f"{fields['tmean'][i] - bands['tmean'][i]:.2f}",
                    f"{fields['tmean'][i] + bands['tmean'][i]:.2f}",
                    f"{fields['tmin'][i] - bands['tmin'][i]:.2f}",
                    f"{fields['tmin'][i] + bands['tmin'][i]:.2f}",
                    f"{max(0.0, fields['pmm'][i] - bands['pmm'][i]):.2f}",
                    f"{fields['pmm'][i] + bands['pmm'][i]:.2f}",
                    f"{max(0.0, et0[i] - bands['tmean'][i] * 0.2):.2f}",
                    f"{et0[i] + bands['tmean'][i] * 0.2:.2f}",
                ]
            )
