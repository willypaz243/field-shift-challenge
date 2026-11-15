"""Scoring de ventanas de siembra (tarea 2.4).

Para cada cultivo y cada ventana de L días (ciclo) dentro de la proyección:

    score = 100 × (0.45·temp + 0.40·agua + 0.15·helada) × erosion

- **temp** (0–1): fracción de días con tmean dentro del rango óptimo del cultivo.
- **agua** (0–1): 1 − min(1, déficit / (2 mm/día × L));
  déficit = Σ max(0, ET₀×Kc − pmm). Mitigado si `drought_tolerant` ≠ "no".
- **helada** (0–1): 1 − sev × (días con tmin < 0)/L, por tolerancia.
- **erosion** (0.5–1.0): penaliza sensibilidad a erosión cerca de drenaje (GAMC).

Confianza: heurística que decae con el horizonte dentro de la proyección.
Top-3: mejores ventanas separadas ≥14 días.

La función es idéntica en servidor y móvil (copia sin dependencias → `scoring_js`).
"""

from __future__ import annotations

import json
from pathlib import Path

FROST_SEV = {"baja": 1.0, "media": 0.5, "alta": 0.2}
DROUGHT_MITIG = {"no": 1.0, "poco": 0.6, "sí": 0.3}
EROSION_PEN = {"alta": 0.5, "media": 0.75}
WATER_ALLOW_PER_DAY = 2.0  # mm/día cubribles por riego/lluvia antes de penalizar
MIN_GAP_DAYS = 14
# POWER (celda 0.5°) nunca baja de 0 °C, pero el valle tiene heladas may–ago.
# Offset heurístico hasta calibrar con estaciones locales (ver EDA.md).
FROST_OFFSET = -2.0


def score_window(
    crop: dict,
    zone: dict,
    tmean: list[float],
    tmin: list[float],
    pmm: list[float],
    et0: list[float],
) -> dict:
    """Score de una ventana. Inputs: arrays de longitud L (días de la ventana)."""
    L = len(tmean)
    lo, hi = crop["temp"]["tmean_opt"]

    # Temperatura
    temp = sum(1 for x in tmean if lo <= x <= hi) / L

    # Helada (con offset de calibración local)
    frost_days = sum(1 for x in tmin if x + FROST_OFFSET < 0)
    sev = FROST_SEV.get(crop.get("helada", {}).get("tolerancia", "baja"), 1.0)
    helada = 1.0 - sev * frost_days / L

    # Agua (déficit = max(0, ET0×Kc − pmm))
    kc = crop.get("kc", {"inicial": 1.0, "medio": 1.0, "final": 1.0})
    kc_avg = (kc["inicial"] + kc["medio"] + kc["final"]) / 3
    deficit = sum(max(0.0, e * kc_avg - p) for e, p in zip(et0, pmm))
    mit = DROUGHT_MITIG.get(crop.get("drought_tolerant", "no"), 1.0)
    agua = 1.0 - min(1.0, deficit * mit / (WATER_ALLOW_PER_DAY * L))

    # Erosión (flag GAMC drenaje)
    erosion = 1.0
    if zone.get("cerca_drenaje") and crop.get("erosion_sens") in EROSION_PEN:
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
    """Top-3 ventanas de siembra para un cultivo.

    `dates`/arrays: proyección diaria (índice 0 = mañana).
    `horizon`: longitud total de la proyección (para la confianza).
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
        # Confianza heurística: decae con el centro de la ventana
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
