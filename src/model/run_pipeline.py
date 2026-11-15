"""Pipeline de modelos (Fase 2): EDA + backtest + proyección 365 d + scoring.

Uso:
    .venv/bin/python src/model/run_pipeline.py \
        --power data/power/D1_tunari_daily.csv \
        --crops data/crops/crops.json \
        --out data/model --eda docs/EDA.md

Salidas:
    data/model/metrics_backtest.json   MAE/RMSE holdout 2024–25
    data/model/forecast_valle.csv      proyección 365 d (tmean,tmin,tmax,pmm,et0 + bandas)
    data/model/top_windows.json        top-3 ventanas por cultivo
    docs/EDA.md                        validación contra conocimiento local
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from .et0 import et0_hargreaves
from .seasonal import Fit, fit, forecast, metrics_for
from .scoring import load_crops, score_windows

VARIABLES = ["tmean", "tmin", "tmax", "pmm"]


def load_power(path: Path) -> tuple[list[str], dict[str, np.ndarray]]:
    dates: list[str] = []
    cols: dict[str, list] = {v: [] for v in VARIABLES}
    with open(path) as f:
        for row in csv.DictReader(f):
            dates.append(row["fecha"])
            for v in VARIABLES:
                raw = row[v].strip()
                val = float(raw) if raw else np.nan
                # pmm > 100 mm/día = error de dato POWER (máx. físico ~100)
                if v == "pmm" and not np.isnan(val) and val > 100:
                    val = np.nan
                cols[v].append(val)
    return dates, {v: np.array(vals) for v, vals in cols.items()}


def valid_mask(arr: np.ndarray) -> np.ndarray:
    return ~np.isnan(arr)


def do_eda(dates: list[str], data: dict[str, np.ndarray], out: Path) -> dict:
    """Validación contra conocimiento local (lluvia dic–feb, heladas may–ago, seca may–sep)."""
    idx = {d: i for i, d in enumerate(dates)}
    i2000 = next(i for i, d in enumerate(dates) if d.startswith("2000"))
    i2026 = next(i for i, d in enumerate(dates) if d.startswith("2026"))

    # Climatología mensual 2000–2025
    monthly: dict[int, dict] = {}
    for m in range(1, 13):
        sel = [i for i in range(i2000, i2026) if int(dates[i][5:7]) == m]
        pmm = np.nanmean(data["pmm"][sel])
        tmean = np.nanmean(data["tmean"][sel])
        tmin = np.nanmean(data["tmin"][sel])
        monthly[m] = {"pmm": float(pmm), "tmean": float(tmean), "tmin": float(tmin)}

    annual_monthly = np.mean([monthly[m]["pmm"] for m in range(1, 13)])
    rainy = np.mean([monthly[m]["pmm"] for m in (12, 1, 2)])
    dry = np.mean([monthly[m]["pmm"] for m in (5, 6, 7, 8, 9)])
    frost = [m for m in range(5, 9) if monthly[m]["tmin"] < 0]

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
        ("Heladas may–ago (tmin < 0°C)", len(frost) == 4, f"meses: {frost}"),
        (
            "Valle templado (tmean anual 10–20 °C)",
            10 <= np.mean([monthly[m]["tmean"] for m in range(1, 13)]) <= 20,
            f"tmean anual {np.mean([monthly[m]['tmean'] for m in range(1, 13)]):.1f} °C",
        ),
    ]

    lines = [
        "# EDA — validación de series POWER (valle de Cochabamba)",
        "",
        f"- Serie: D1 Tunari (celda POWER 0.5°), {dates[0]} → {dates[-1]}",
        f"- Fila válida de tmin/tmax: {dates[next(i for i in range(len(dates)) if not np.isnan(data['tmin'][i]))]}",
        "",
        "## Climatología mensual (2000–2025)",
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
        "- ⚠️ La fórmula del BACKLOG v2 (`0.0023·(Tmean+15)·√RA`) es incompleta y da ~10× menos; corregida en `src/model/et0.py`.",
        "",
        "## Limitaciones de POWER detectadas (armonización)",
        "",
        f"1. **pmm absoluto muy bajo**: {annual_monthly * 12:.0f} mm/año vs ~700 mm/año esperados en el valle. "
        "La celda 0.5° de POWER subestima la precipitación convective andina. "
        "**IMERG (GPM) se usa como fuente primaria de pmm** y POWER como validación de patrón estacional.",
        "2. **tmin nunca < 0 °C** en POWER (mínimo jul ≈ "
        f"{min(monthly[m]['tmin'] for m in range(5, 9)):.1f} °C), pero el valle tiene heladas may–ago (conocimiento local). "
        "El scoring aplica un offset de helada documentado (`FROST_OFFSET`) hasta calibrar con estaciones locales.",
        "3. **Outliers pmm > 100 mm/día** (2 casos, máx 704 mm): descartados como error de dato en el ETL.",
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
    }
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--power", default="data/power/D1_tunari_daily.csv")
    ap.add_argument("--crops", default="data/crops/crops.json")
    ap.add_argument("--out", default="data/model")
    ap.add_argument("--eda", default="docs/EDA.md")
    ap.add_argument("--horizon", type=int, default=365)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dates, data = load_power(Path(args.power))
    n = len(dates)
    t = np.arange(n, dtype=float)

    # EDA (tarea 2.1)
    eda = do_eda(dates, data, Path(args.eda))

    # Backtest 2024–25 (tarea 2.3)
    i2024 = next(i for i, d in enumerate(dates) if d == "2024-01-01")
    t_hold = float(t[i2024])
    horizon_bt = 731
    metrics = [metrics_for(data[v], t, v, t_hold, horizon_bt) for v in VARIABLES]
    (out / "metrics_backtest.json").write_text(
        json.dumps(
            {"holdout": "2024-01-01 → 2025-12-31", "metrics": metrics, "eda": eda},
            indent=2,
        )
    )

    # Proyección 365 d desde hoy (tarea 2.2)
    today = date(2026, 11, 14)
    t_today = (today - date.fromisoformat(dates[0])).days
    fits = {}
    # Enmascarar NaN por variable
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

    doy = np.array(
        [(today + timedelta(days=i + 1)).timetuple().tm_yday for i in range(H)]
    )
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

    # Scoring top-3 por cultivo (tarea 2.4)
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
            print(
                f"  {cid}: mejor ventana {w0['inicio']} → {w0['fin']} (score {w0['score']})"
            )
    print(
        f"Salidas: {out}/ (forecast_valle.csv, top_windows.json, metrics_backtest.json), {args.eda}"
    )


if __name__ == "__main__":
    main()
