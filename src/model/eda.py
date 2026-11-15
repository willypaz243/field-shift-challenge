"""EDA: validation of the climate series against local knowledge.

Checks the expected valley patterns (Dec-Feb rain, May-Aug frost, May-Sep
dry season, mild annual temperature) and renders the Markdown report with
the source-harmonization decisions.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import numpy as np

from .history import HistorySeries


class EdaReport:
    """Monthly climatology, local-knowledge checks and Markdown rendering."""

    def __init__(self, series: HistorySeries, db: Path, zone_id: str) -> None:
        self.series = series
        self.db = db
        self.zone_id = zone_id
        self.monthly = self._monthly_climatology()
        self.annual_monthly = float(np.mean([self.monthly[m]["pmm"] for m in range(1, 13)]))
        self.rainy = float(np.mean([self.monthly[m]["pmm"] for m in (12, 1, 2)]))
        self.dry = float(np.mean([self.monthly[m]["pmm"] for m in (5, 6, 7, 8, 9)]))
        # Frost is a daily-minimum phenomenon: the monthly mean stays above 0
        # even in months with freezing nights.
        self.tmin_min_by_month = self._tmin_min_by_month()
        self.frost_months = [m for m in range(5, 9) if self.tmin_min_by_month[m] < 0]
        self.tmin_min = min(self.tmin_min_by_month.values())
        imerg_annual, power_annual = self._annual_precipitation()
        self.imerg_annual = imerg_annual
        self.power_annual = power_annual

    def _monthly_climatology(self) -> dict[int, dict[str, float]]:
        dates, data = self.series.dates, self.series.fields
        monthly: dict[int, dict[str, float]] = {}
        for m in range(1, 13):
            sel = [i for i, d in enumerate(dates) if int(d[5:7]) == m]
            monthly[m] = {
                "pmm": float(np.nanmean(data["pmm"][sel])),
                "tmean": float(np.nanmean(data["tmean"][sel])),
                "tmin": float(np.nanmean(data["tmin"][sel])),
            }
        return monthly

    def _tmin_min_by_month(self) -> dict[int, float]:
        dates, data = self.series.dates, self.series.fields
        return {
            m: float(np.nanmin(data["tmin"][[i for i, d in enumerate(dates) if int(d[5:7]) == m]]))
            for m in range(5, 9)
        }

    def _annual_precipitation(self) -> tuple[float, float]:
        con = sqlite3.connect(self.db)
        try:
            s_imerg, s_power = con.execute(
                "SELECT SUM(pmm_sat), SUM(pmm) FROM climate_history "
                "WHERE zone_id = ? AND pmm_sat IS NOT NULL",
                (self.zone_id,),
            ).fetchone()
        finally:
            con.close()
        n_days = self.series.n_days
        imerg = 0.0 if s_imerg is None else float(s_imerg)
        power = 0.0 if s_power is None else float(s_power)
        return (imerg / n_days * 365.25, power / n_days * 365.25)

    def checks(self) -> list[tuple[str, bool, str]]:
        mean_tmean = np.mean([self.monthly[m]["tmean"] for m in range(1, 13)])
        return [
            (
                "Lluvia concentrada dic–feb (>2× mensual anual)",
                self.rainy > 2 * self.annual_monthly,
                f"{self.rainy:.1f} vs {self.annual_monthly:.1f} mm/mes",
            ),
            (
                "Sequía may–sep (<25% de la época lluviosa)",
                self.dry < 0.25 * self.rainy,
                f"{self.dry:.1f} vs {self.rainy:.1f} mm/mes",
            ),
            (
                "Heladas may–ago (mínimo diario tmin < 0°C)",
                len(self.frost_months) == 4,
                "meses: "
                f"{self.frost_months} (mínimos: "
                + ", ".join(f"{m:02d} {v:.1f}" for m, v in self.tmin_min_by_month.items())
                + ")",
            ),
            (
                "Valle templado (tmean anual 10–20 °C)",
                10 <= mean_tmean <= 20,
                f"tmean anual {mean_tmean:.1f} °C",
            ),
        ]

    def summary(self) -> dict[str, Any]:
        checks = self.checks()
        return {
            "rainy_dec_feb_mm": round(self.rainy, 1),
            "dry_may_sep_mm": round(self.dry, 1),
            "frost_months": self.frost_months,
            "checks_passed": sum(1 for _, ok, _ in checks if ok),
            "checks_total": len(checks),
            "pmm_imerg_mm_y": round(self.imerg_annual),
            "pmm_power_mm_y": round(self.power_annual),
        }

    def render(self) -> str:
        dates = self.series.dates
        lines = [
            "# EDA — validación de series (valle de Cochabamba)",
            "",
            f"- Serie: {self.zone_id} (DB consolidada `{self.db.name}`), {dates[0]} → {dates[-1]}",
            "- `pmm` = IMERG `pmm_sat` (primaria); POWER como fallback.",
            "",
            "## Climatología mensual (2016–2025)",
            "",
            "| Mes | pmm (mm) | tmean (°C) | tmin (°C) |",
            "|---|---|---|---|",
        ]
        for m in range(1, 13):
            lines.append(
                f"| {m:02d} | {self.monthly[m]['pmm']:.1f} | {self.monthly[m]['tmean']:.1f} | {self.monthly[m]['tmin']:.1f} |"
            )
        lines += ["", "## Verificación contra conocimiento local", ""]
        for name, ok, detail in self.checks():
            lines.append(f"- {'✅' if ok else '❌'} {name} — {detail}")
        lines += [
            "",
            "## ET₀ Hargreaves (FAO-56 Ec. 52)",
            "",
            "- Fórmula: `ET₀ = 0.0023·(Tmean+17.8)·√(Tmax−Tmin)·Ra` con Ra en mm/día (0.408×MJ/m²).",
            "",
            "## Armonización de fuentes (decisiones)",
            "",
            f"1. **pmm**: IMERG {self.imerg_annual:.0f} mm/año vs POWER {self.power_annual:.0f} mm/año "
            "(2016–2025). POWER (celda 0.5°) subestima la lluvia convectiva andina; "
            "IMERG (0.1°) es la fuente primaria y POWER queda como validación de patrón.",
            f"2. **tmin**: POWER llega a {self.tmin_min:.1f} °C (may–ago), coherente con heladas "
            "locales. Con tmin real sub-cero, `FROST_OFFSET = 0.0` en el scoring "
            "(el offset se mantiene como gancho de calibración con estaciones locales).",
            "3. **Outliers pmm > 100 mm/día**: descartados como error de dato (NaN).",
            "",
        ]
        return "\n".join(lines)

    def write(self, out: Path) -> None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.render())
