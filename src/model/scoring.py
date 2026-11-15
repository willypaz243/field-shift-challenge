"""Planting-window scoring (tasks 2.4 and 12a).

Reference implementation shared by the server and the mobile app. The
mobile side must reproduce it exactly; the published test vectors
(`data/model/test_vectors.json`) are the portability contract.

For each L-day window (crop cycle) inside the forecast:

    score = 100 * (0.45*temp + 0.40*water + 0.15*frost) * erosion

- **temp** (0-1): fraction of days with tmean inside the crop's optimal range.
- **water** (0-1): 1 - min(1, deficit / (2 mm/day * L));
  deficit = sum(max(0, ET0*Kc - pmm)). Mitigated when `drought_tolerant` != "no".
- **frost** (0-1): 1 - sev * (days with tmin < 0) / L, by tolerance.
- **erosion** (0.5-1.0): penalizes erosion sensitivity near drainage (GAMC).

Output of `score_window`:
- `score` (0-100, 1 decimal)
- `veredicto`: `bueno` (>= 70), `con_cuidado` (>= 40), `malo`; thresholds
  configurable (`umbral_bueno` / `umbral_malo`)
- `confianza`: heuristic that decays with the window center inside the
  forecast (base 0.7 when no horizon is given)
- `motivos`: codes, not sentences (the app translates them via i18n).
  Each code appears iff the matching displayed `detalle` value is nonzero:
  - `temp_fuera_rango`: some days outside the optimal temperature range
  - `deficit_agua`: deficit over the crop water demand
  - `heladas`: days with sub-zero tmin
  - `erosion_riesgo`: erosion-sensitive crop near drainage
- `detalle`: per-component values (temp, agua, helada, erosion, deficit_mm,
  frost_days)

Top-3: best windows separated by >= 14 days.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FROST_SEV = {"baja": 1.0, "media": 0.5, "alta": 0.2}
DROUGHT_MITIG = {"no": 1.0, "poco": 0.6, "sí": 0.3}
EROSION_PEN = {"alta": 0.5, "media": 0.75}
WATER_ALLOW_PER_DAY = 2.0  # mm/day coverable by rain/irrigation before penalizing
MIN_GAP_DAYS = 14
# The EDA (2016-2025) confirms real sub-zero tmin days (D1: 194 days, min -3.92 C),
# so observed tmin already captures frost; the offset stays 0.0 as a calibration
# hook for local stations (see EDA.md).
FROST_OFFSET = 0.0
# Verdict thresholds (API-CONTRACT §2): >= 70 bueno, >= 40 con_cuidado, else malo.
VERDICT_GOOD = 70.0
VERDICT_POOR = 40.0
BASE_CONFIDENCE = 0.7


def veredicto(
    score: float,
    umbral_bueno: float = VERDICT_GOOD,
    umbral_malo: float = VERDICT_POOR,
) -> str:
    """Map a 0-100 score to a verdict. Thresholds are configurable."""
    if score >= umbral_bueno:
        return "bueno"
    if score >= umbral_malo:
        return "con_cuidado"
    return "malo"


def _confianza(L: int, horizon: int | None, pos: int) -> float:
    """Heuristic confidence: decays with the window center in the forecast."""
    if horizon is None or horizon <= 0:
        return BASE_CONFIDENCE
    center = (pos + L / 2) / horizon
    return max(0.4, min(0.9, 0.92 - 0.5 * center))


def score_window(
    crop: dict[str, Any],
    zone: dict[str, Any],
    tmean: list[float],
    tmin: list[float],
    pmm: list[float],
    et0: list[float],
    horizon: int | None = None,
    pos: int = 0,
    umbral_bueno: float = VERDICT_GOOD,
    umbral_malo: float = VERDICT_POOR,
) -> dict[str, Any]:
    """Score one window. Inputs: arrays of length L (window days).

    `crop`: entry of `crops.json`; `zone`: dict with `cerca_drenaje`
    (meters to the nearest drainage, or None). `horizon`/`pos` locate the
    window inside the forecast for the confidence.
    """
    L = len(tmean)
    lo, hi = crop["temp"]["tmean_opt"]

    # Temperature
    temp = sum(1 for x in tmean if lo <= x <= hi) / L

    # Frost (with local calibration offset)
    frost_days = sum(1 for x in tmin if x + FROST_OFFSET < 0)
    sev = FROST_SEV.get(crop.get("helada", {}).get("tolerancia", "baja"), 1.0)
    helada = 1.0 - sev * frost_days / L

    # Water (deficit = max(0, ET0*Kc - pmm))
    kc = crop.get("kc", {"inicial": 1.0, "medio": 1.0, "final": 1.0})
    kc_avg = (kc["inicial"] + kc["medio"] + kc["final"]) / 3
    deficit = sum(max(0.0, e * kc_avg - p) for e, p in zip(et0, pmm, strict=False))
    mit = DROUGHT_MITIG.get(crop.get("drought_tolerant", "no"), 1.0)
    agua = 1.0 - min(1.0, deficit * mit / (WATER_ALLOW_PER_DAY * L))

    # Erosion: cerca_drenaje is meters to the nearest drainage (GAMC);
    # a value means within 200 m, None means not within 200 m.
    erosion = 1.0
    if zone.get("cerca_drenaje") is not None and crop.get("erosion_sens") in EROSION_PEN:
        erosion = EROSION_PEN[crop["erosion_sens"]]

    score = round(100.0 * (0.45 * temp + 0.40 * agua + 0.15 * helada) * erosion, 1)

    # Reasons are derived from the displayed values so the mobile port
    # reproduces them without extra floating-point decisions.
    motivos: list[str] = []
    if round(temp, 2) < 1.0:
        motivos.append("temp_fuera_rango")
    if round(deficit, 1) > 0:
        motivos.append("deficit_agua")
    if frost_days > 0:
        motivos.append("heladas")
    if erosion < 1.0:
        motivos.append("erosion_riesgo")

    return {
        "score": score,
        "veredicto": veredicto(score, umbral_bueno, umbral_malo),
        "confianza": round(_confianza(L, horizon, pos), 2),
        "motivos": motivos,
        "detalle": {
            "temp": round(temp, 2),
            "agua": round(agua, 2),
            "helada": round(helada, 2),
            "erosion": erosion,
            "deficit_mm": round(deficit, 1),
            "frost_days": frost_days,
        },
    }


def score_windows(
    crop: dict[str, Any],
    zone: dict[str, Any],
    dates: list[str],
    tmean: list[float],
    tmin: list[float],
    pmm: list[float],
    et0: list[float],
    horizon: int | None = None,
    umbral_bueno: float = VERDICT_GOOD,
    umbral_malo: float = VERDICT_POOR,
) -> list[dict[str, Any]]:
    """Top-3 planting windows for a crop.

    `dates`/arrays: daily forecast (index 0 = tomorrow).
    `horizon`: total forecast length (used for the confidence).
    """
    L = int(round(sum(crop["ciclo_dias"]) / 2))
    H = len(dates)
    horizon = H if horizon is None else horizon
    scored: list[dict[str, Any]] = []
    for s in range(0, H - L + 1):
        det = score_window(
            crop,
            zone,
            tmean[s : s + L],
            tmin[s : s + L],
            pmm[s : s + L],
            et0[s : s + L],
            horizon=horizon,
            pos=s,
            umbral_bueno=umbral_bueno,
            umbral_malo=umbral_malo,
        )
        scored.append(
            {
                "inicio": dates[s],
                "fin": dates[s + L - 1],
                "score": det["score"],
                "veredicto": det["veredicto"],
                "confianza": det["confianza"],
                "motivos": det["motivos"],
                "detalle": det["detalle"],
            }
        )

    scored.sort(key=lambda w: w["score"], reverse=True)
    top: list[dict[str, Any]] = []
    for w in scored:
        if all(abs(_day(w["inicio"]) - _day(t["inicio"])) >= MIN_GAP_DAYS for t in top):
            top.append(w)
        if len(top) == 3:
            break
    return top


def _day(iso: str) -> int:
    y, m, d = map(int, iso.split("-"))
    return (y - 2026) * 365 + m * 31 + d


def load_crops(path: str | Path = "data/crops/crops.json") -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text())["crops"]
