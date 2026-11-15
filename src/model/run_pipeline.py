"""Model pipeline (Phase 2): EDA + backtest + 365-day forecast + scoring.

History is read from the consolidated DB (valle.db), not from loose CSVs:
the common range of all sources (POWER 1984+, IMERG 2016+, SMAP 2015+) is
2016-01-01 to 2025-12-31 and is the training window. `pmm` uses IMERG
(`pmm_sat`) as the primary source (the 0.5 deg POWER cell underestimates
Andean convective rain) with POWER `pmm` as fallback.

Usage:
    .venv/bin/python -m src.model.run_pipeline \
        --db data/db/valle.db \
        --crops data/crops/crops.json \
        --out data/model --eda docs/EDA.md

Outputs:
    data/model/metrics_backtest.json   MAE/RMSE holdout 2024-25
    data/model/forecast_valle.csv      365-day forecast (tmean,tmin,tmax,pmm,et0 + bands)
    data/model/top_windows.json        top-3 windows per crop
    docs/EDA.md                        validation against local knowledge
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .backtest import Backtester
from .eda import EdaReport
from .forecast import ForecastBuilder, write_forecast_csv
from .history import HistorySeries, load_history  # noqa: F401  (re-exported)
from .scoring import load_crops, score_windows

ROOT = Path(__file__).resolve().parents[2]
HISTORY_START = "2016-01-01"
HISTORY_END = "2025-12-31"
HOLDOUT_START = "2024-01-01"
BACKTEST_HORIZON = 731
# Valley-wide series: no zone-level drainage data in this cut (None = not within 200 m)
VALLEY_ZONE = {"cerca_drenaje": None, "elev_m": 3126}


class Pipeline:
    """EDA + backtest + forecast + scoring, writing all outputs."""

    def __init__(
        self,
        db: Path,
        zone: str,
        start: str,
        end: str,
        crops: str | Path,
        out: Path,
        eda: str | Path,
        horizon: int = 365,
        today: date | None = None,
    ) -> None:
        self.db = db
        self.zone = zone
        self.start = start
        self.end = end
        self.crops = crops
        self.out = out
        self.eda = eda
        self.horizon = horizon
        self.today = today

    def run(self) -> dict:
        self.out.mkdir(parents=True, exist_ok=True)
        series = load_history(self.db, self.zone, self.start, self.end)

        eda = EdaReport(series, self.db, self.zone)
        eda.write(Path(self.eda))
        eda_summary = eda.summary()

        metrics = Backtester(series, BACKTEST_HORIZON).metrics(HOLDOUT_START)
        (self.out / "metrics_backtest.json").write_text(
            json.dumps(
                {
                    "holdout": f"{HOLDOUT_START} → {self.end}",
                    "window": f"{self.start} → {self.end}",
                    "metrics": metrics,
                    "eda": eda_summary,
                },
                indent=2,
            )
        )

        today = self.today if self.today is not None else date.today()
        result = ForecastBuilder(series, self.horizon, today).build()
        write_forecast_csv(result, self.out / "forecast_valle.csv")

        top = {
            c["id"]: score_windows(
                c,
                VALLEY_ZONE,
                result.dates,
                [float(x) for x in result.fields["tmean"]],
                [float(x) for x in result.fields["tmin"]],
                [float(x) for x in result.fields["pmm"]],
                [float(x) for x in result.et0],
            )
            for c in load_crops(self.crops)
        }
        (self.out / "top_windows.json").write_text(json.dumps(top, indent=2, ensure_ascii=False))

        self._print_summary(eda_summary, metrics, top)
        return eda_summary

    def _print_summary(self, eda: dict, metrics: list[dict], top: dict) -> None:
        print(f"EDA: {eda['checks_passed']}/{eda['checks_total']} checks OK")
        for m in metrics:
            print(f"  {m['variable']}: MAE={m['mae']} RMSE={m['rmse']}")
        for cid, wins in top.items():
            if wins:
                w0 = wins[0]
                print(f"  {cid}: best window {w0['inicio']} -> {w0['fin']} (score {w0['score']})")
        print(
            f"Outputs: {self.out}/ (forecast_valle.csv, top_windows.json, metrics_backtest.json), {self.eda}"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/db/valle.db")
    ap.add_argument("--zone", default="D1_tunari")
    ap.add_argument("--start", default=HISTORY_START)
    ap.add_argument("--end", default=HISTORY_END)
    ap.add_argument("--crops", default="data/crops/crops.json")
    ap.add_argument("--out", default="data/model")
    ap.add_argument("--eda", default="docs/EDA.md")
    ap.add_argument("--horizon", type=int, default=365)
    ap.add_argument("--today", default=None, help="ISO date; default = system date")
    args = ap.parse_args()

    today = date.fromisoformat(args.today) if args.today else None
    Pipeline(
        ROOT / args.db,
        args.zone,
        args.start,
        args.end,
        args.crops,
        Path(args.out),
        args.eda,
        horizon=args.horizon,
        today=today,
    ).run()


if __name__ == "__main__":
    main()
