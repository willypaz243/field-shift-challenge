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
import csv
import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from .et0 import et0_hargreaves
from .scoring import load_crops, score_windows
from .seasonal import fit, forecast, metrics_for

ROOT = Path(__file__).resolve().parents[2]
VARIABLES = ["tmean", "tmin", "tmax", "pmm"]
HISTORY_START = "2016-01-01"
HISTORY_END = "2025-12-31"


def load_history(
    db: Path, zone_id: str, start: str, end: str
) -> tuple[list[str], dict[str, np.ndarray]]:
    """Read `climate_history` from the consolidated DB for one zone.

    `pmm` = `pmm_sat` (IMERG, primary) with POWER `pmm` as fallback; values
    above 100 mm/day are treated as data errors (NaN).
    """
    con = sqlite3.connect(db)
    try:
        rows = con.execute(
            "SELECT fecha, tmean, tmin, tmax, pmm, pmm_sat FROM climate_history "
            "WHERE zone_id = ? AND fecha >= ? AND fecha <= ? ORDER BY fecha",
            (zone_id, start, end),
        ).fetchall()
    finally:
        con.close()
    dates: list[str] = []
    cols: dict[str, list] = {v: [] for v in VARIABLES}
    for fecha, tmean, tmin, tmax, pmm, pmm_sat in rows:
        dates.append(fecha)
        cols["tmean"].append(tmean)
        cols["tmin"].append(tmin)
        cols["tmax"].append(tmax)
        sat = pmm_sat if (pmm_sat is not None and pmm_sat <= 100) else None
        cols["pmm"].append(sat if sat is not None else pmm)
    arrays: dict[str, np.ndarray] = {}
    for v in VARIABLES:
        arr = np.array([None if x is None else float(x) for x in cols[v]], dtype=float)
        if v == "pmm":
            arr[arr > 100] = np.nan
        arrays[v] = arr
    return dates, arrays


def valid_mask(arr: np.ndarray) -> np.ndarray:
    return ~np.isnan(arr)


def do_eda(
    db: Path, zone_id: str, dates: list[str], data: dict[str, np.ndarray], out: Path
) -> dict:
    """Validation against local knowledge (Dec-Feb rain, May-Aug frost, May-Sep dry season)."""
    monthly: dict[int, dict] = {}
    for m in range(1, 13):
        sel = [i for i, d in enumerate(dates) if int(d[5:7]) == m]
        monthly[m] = {
            "pmm": float(np.nanmean(data["pmm"][sel])),
            "tmean": float(np.nanmean(data["tmean"][sel])),
            "tmin": float(np.nanmean(data["tmin"][sel])),
        }

    annual_monthly = np.mean([monthly[m]["pmm"] for m in range(1, 13)])
    rainy = np.mean([monthly[m]["pmm"] for m in (12, 1, 2)])
    dry = np.mean([monthly[m]["pmm"] for m in (5, 6, 7, 8, 9)])
    # Frost is a daily-minimum phenomenon: the monthly mean stays above 0
    # even in months with freezing nights.
    tmin_min_by_month: dict[int, float] = {}
    for m in range(5, 9):
        sel = [i for i, d in enumerate(dates) if int(d[5:7]) == m]
        tmin_min_by_month[m] = float(np.nanmin(data["tmin"][sel]))
    frost = [m for m in range(5, 9) if tmin_min_by_month[m] < 0]
    tmin_min = min(tmin_min_by_month.values())

    checks = [
        (
            "Lluvia concentrada dic–feb (>2× mensual anual)",
            rainy > 2 * annual_monthly,
            f"{rainy:.1f} vs {annual_monthly:.1f} mm/mes",
        ),
        (
            "Sequía may–sep (<25% de la época lluviosa)",
            dry < 0.25 * rainy,
            f"{dry:.1f} vs {rainy:.1f} mm/mes",
        ),
        (
            "Heladas may–ago (mínimo diario tmin < 0°C)",
            len(frost) == 4,
            f"meses: {frost} (mínimos: "
            + ", ".join(f"{m:02d} {v:.1f}" for m, v in tmin_min_by_month.items())
            + ")",
        ),
        (
            "Valle templado (tmean anual 10–20 °C)",
            10 <= np.mean([monthly[m]["tmean"] for m in range(1, 13)]) <= 20,
            f"tmean anual {np.mean([monthly[m]['tmean'] for m in range(1, 13)]):.1f} °C",
        ),
    ]

    con = sqlite3.connect(db)
    try:
        s_imerg, s_power = con.execute(
            "SELECT SUM(pmm_sat), SUM(pmm) FROM climate_history "
            "WHERE zone_id = ? AND pmm_sat IS NOT NULL",
            (zone_id,),
        ).fetchone()
    finally:
        con.close()
    n_days = len(dates)
    imerg_annual = (s_imerg or 0) / n_days * 365.25
    power_annual = (s_power or 0) / n_days * 365.25

    lines = [
        "# EDA — validación de series (valle de Cochabamba)",
        "",
        f"- Serie: {zone_id} (DB consolidada `{db.name}`), {dates[0]} → {dates[-1]}",
        "- `pmm` = IMERG `pmm_sat` (primaria); POWER como fallback.",
        "",
        "## Climatología mensual (2016–2025)",
        "",
        "| Mes | pmm (mm) | tmean (°C) | tmin (°C) |",
        "|---|---|---|---|",
    ]
    for m in range(1, 13):
        lines.append(
            f"| {m:02d} | {monthly[m]['pmm']:.1f} | {monthly[m]['tmean']:.1f} | {monthly[m]['tmin']:.1f} |"
        )
    lines += ["", "## Verificación contra conocimiento local", ""]
    for name, ok, detail in checks:
        lines.append(f"- {'✅' if ok else '❌'} {name} — {detail}")
    lines += [
        "",
        "## ET₀ Hargreaves (FAO-56 Ec. 52)",
        "",
        "- Fórmula: `ET₀ = 0.0023·(Tmean+17.8)·√(Tmax−Tmin)·Ra` con Ra en mm/día (0.408×MJ/m²).",
        "",
        "## Armonización de fuentes (decisiones)",
        "",
        f"1. **pmm**: IMERG {imerg_annual:.0f} mm/año vs POWER {power_annual:.0f} mm/año "
        "(2016–2025). POWER (celda 0.5°) subestima la lluvia convectiva andina; "
        "IMERG (0.1°) es la fuente primaria y POWER queda como validación de patrón.",
        f"2. **tmin**: POWER llega a {tmin_min:.1f} °C (may–ago), coherente con heladas "
        "locales. El scoring sigue aplicando `FROST_OFFSET = -2.0` como heurística "
        "documentada hasta calibrar con estaciones locales.",
        "3. **Outliers pmm > 100 mm/día**: descartados como error de dato (NaN).",
        "",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))

    summary = {
        "rainy_dec_feb_mm": round(rainy, 1),
        "dry_may_sep_mm": round(dry, 1),
        "frost_months": frost,
        "checks_passed": sum(1 for _, ok, _ in checks if ok),
        "checks_total": len(checks),
        "pmm_imerg_mm_y": round(imerg_annual),
        "pmm_power_mm_y": round(power_annual),
    }
    return summary


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

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dates, data = load_history(ROOT / args.db, args.zone, args.start, args.end)
    n = len(dates)
    t = np.arange(n, dtype=float)

    # EDA (task 2.1)
    eda = do_eda(ROOT / args.db, args.zone, dates, data, Path(args.eda))

    # Backtest 2024-25 (task 2.3)
    i2024 = next(i for i, d in enumerate(dates) if d == "2024-01-01")
    t_hold = float(t[i2024])
    horizon_bt = 731
    metrics = [metrics_for(data[v], t, v, t_hold, horizon_bt) for v in VARIABLES]
    (out / "metrics_backtest.json").write_text(
        json.dumps(
            {
                "holdout": "2024-01-01 → 2025-12-31",
                "window": f"{args.start} → {args.end}",
                "metrics": metrics,
                "eda": eda,
            },
            indent=2,
        )
    )

    # 365-day forecast from today (task 2.2)
    today = date.fromisoformat(args.today) if args.today else date.today()
    t_today = (today - date.fromisoformat(dates[0])).days
    fits = {}
    # Mask NaN per variable
    for v in VARIABLES:
        m = valid_mask(data[v])
        fits[v] = fit(data[v][m], t[m])

    H = args.horizon
    fdates = [(today + timedelta(days=i + 1)).isoformat() for i in range(H)]
    arrays: dict[str, np.ndarray] = {}
    bands: dict[str, np.ndarray] = {}
    for v in VARIABLES:
        h, mean, band = forecast(fits[v], H, t_start=float(t_today))
        arrays[v] = np.clip(mean, 0, None) if v == "pmm" else mean
        bands[v] = band

    doy = np.array([(today + timedelta(days=i + 1)).timetuple().tm_yday for i in range(H)])
    et0 = et0_hargreaves(arrays["tmean"], arrays["tmax"], arrays["tmin"], doy)
    et0 = np.clip(et0, 0, None)

    with open(out / "forecast_valle.csv", "w", newline="") as f:
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
        for i, fd in enumerate(fdates):
            w.writerow(
                [
                    fd,
                    f"{arrays['tmean'][i]:.2f}",
                    f"{arrays['tmin'][i]:.2f}",
                    f"{arrays['tmax'][i]:.2f}",
                    f"{arrays['pmm'][i]:.2f}",
                    f"{et0[i]:.2f}",
                    f"{arrays['tmean'][i] - bands['tmean'][i]:.2f}",
                    f"{arrays['tmean'][i] + bands['tmean'][i]:.2f}",
                    f"{arrays['tmin'][i] - bands['tmin'][i]:.2f}",
                    f"{arrays['tmin'][i] + bands['tmin'][i]:.2f}",
                    f"{max(0.0, arrays['pmm'][i] - bands['pmm'][i]):.2f}",
                    f"{arrays['pmm'][i] + bands['pmm'][i]:.2f}",
                    f"{max(0.0, et0[i] - bands['tmean'][i] * 0.2):.2f}",
                    f"{et0[i] + bands['tmean'][i] * 0.2:.2f}",
                ]
            )

    # Top-3 scoring per crop (task 2.4)
    zone = {"cerca_drenaje": False, "elev_m": 3126}
    top = {
        c["id"]: score_windows(
            c,
            zone,
            fdates,
            [float(x) for x in arrays["tmean"]],
            [float(x) for x in arrays["tmin"]],
            [float(x) for x in arrays["pmm"]],
            [float(x) for x in et0],
        )
        for c in load_crops(args.crops)
    }
    (out / "top_windows.json").write_text(json.dumps(top, indent=2, ensure_ascii=False))

    print(f"EDA: {eda['checks_passed']}/{eda['checks_total']} checks OK")
    for m in metrics:
        print(f"  {m['variable']}: MAE={m['mae']} RMSE={m['rmse']}")
    for cid, wins in top.items():
        if wins:
            w0 = wins[0]
            print(f"  {cid}: best window {w0['inicio']} -> {w0['fin']} (score {w0['score']})")
    print(
        f"Outputs: {out}/ (forecast_valle.csv, top_windows.json, metrics_backtest.json), {args.eda}"
    )


if __name__ == "__main__":
    main()
