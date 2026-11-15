"""Planting-window scoring (task 2.4).

For each crop and each L-day window (cycle) inside the forecast:

    score = 100 * (0.45*temp + 0.40*water + 0.15*frost) * erosion

- **temp** (0-1): fraction of days with tmean inside the crop's optimal range.
- **water** (0-1): 1 - min(1, deficit / (2 mm/day * L));
  deficit = sum(max(0, ET0*Kc - pmm)). Mitigated when `drought_tolerant` != "no".
- **frost** (0-1): 1 - sev * (days with tmin < 0) / L, by tolerance.
- **erosion** (0.5-1.0): penalizes erosion sensitivity near drainage (GAMC).

Confidence: heuristic that decays with the horizon inside the forecast.
Top-3: best windows separated by >= 14 days.

The function is identical on server and mobile (dependency-free copy -> `scoring_js`).
"""

from __future__ import annotations

import json
from pathlib import Path

FROST_SEV = {"baja": 1.0, "media": 0.5, "alta": 0.2}
DROUGHT_MITIG = {"no": 1.0, "poco": 0.6, "sí": 0.3}
EROSION_PEN = {"alta": 0.5, "media": 0.75}
WATER_ALLOW_PER_DAY = 2.0  # mm/day coverable by rain/irrigation before penalizing
MIN_GAP_DAYS = 14
# The EDA (2016-2025) confirms real sub-zero tmin days (D1: 194 days, min -3.92 C),
# so observed tmin already captures frost; the offset stays 0.0 as a calibration
# hook for local stations (see EDA.md).
FROST_OFFSET = 0.0


def score_window(
    crop: dict,
    zone: dict,
    tmean: list[float],
    tmin: list[float],
    pmm: list[float],
    et0: list[float],
) -> dict:
    """Score one window. Inputs: arrays of length L (window days)."""
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

    score = 100.0 * (0.45 * temp + 0.40 * agua + 0.15 * helada) * erosion
    return {
        "score": round(score, 1),
        "temp": round(temp, 2),
        "agua": round(agua, 2),
        "helada": round(helada, 2),
        "erosion": erosion,
        "deficit_mm": round(deficit, 1),
        "frost_days": frost_days,
    }


def score_windows(
    crop: dict,
    zone: dict,
    dates: list[str],
    tmean: list[float],
    tmin: list[float],
    pmm: list[float],
    et0: list[float],
    horizon: int | None = None,
) -> list[dict]:
    """Top-3 planting windows for a crop.

    `dates`/arrays: daily forecast (index 0 = tomorrow).
    `horizon`: total forecast length (used for the confidence).
    """
    L = int(round(sum(crop["ciclo_dias"]) / 2))
    H = len(dates)
    horizon = H if horizon is None else horizon
    scored = []
    for s in range(0, H - L + 1):
        det = score_window(
            crop,
            zone,
            tmean[s : s + L],
            tmin[s : s + L],
            pmm[s : s + L],
            et0[s : s + L],
        )
        # Heuristic confidence: decays with the window center
        center = (s + L / 2) / horizon
        conf = max(0.4, min(0.9, 0.92 - 0.5 * center))
        scored.append(
            {
                "inicio": dates[s],
                "fin": dates[s + L - 1],
                "score": det["score"],
                "confianza": round(conf, 2),
                "detalle": det,
            }
        )

    scored.sort(key=lambda w: w["score"], reverse=True)
    top: list[dict] = []
    for w in scored:
        if all(abs(_day(w["inicio"]) - _day(t["inicio"])) >= MIN_GAP_DAYS for t in top):
            top.append(w)
        if len(top) == 3:
            break
    return top


def _day(iso: str) -> int:
    y, m, d = map(int, iso.split("-"))
    return (y - 2026) * 365 + m * 31 + d


def load_crops(path: str | Path = "data/crops/crops.json") -> list[dict]:
    return json.loads(Path(path).read_text())["crops"]
