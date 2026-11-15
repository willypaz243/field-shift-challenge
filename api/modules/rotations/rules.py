"""Rotation rules derived from the crop catalog (`data/crops/crops.json`).

Every rule reads a field of the catalog, so each score can be traced to its
source. They are explainable agronomic heuristics, not a validated table:
the service marks the result with medium or low confidence, and the data team
can replace them (issue #41) by writing a table in the same shape.
"""

from __future__ import annotations

from typing import Any

Crop = dict[str, Any]

# 1 (worst) to 3 (best) per goal, as in API-CONTRACT §4.
WATER_BY_DEMAND = {"baja": 3, "media-baja": 3, "media": 2, "alta": 1, "muy alta": 1}
FORAGE_BY_VALUE = {"alto": 3, "medio": 2, "bajo": 1}
# Local demand documented in the catalog's `mercado` text (SITAP tonnage, markets
# in the city, "demanda segura"); there are no price data, hence "falta saber".
SELLS_WELL = {
    "papa": 3,
    "choclo": 3,
    "lechuga": 3,
    "hortalizas": 3,
    "flores": 3,
    "durazno": 3,
    "quinua": 3,
    "trigo": 2,
    "papaliza": 2,
    "haba": 2,
    "tarwi": 1,
    "alfalfa": 2,
    "avena": 1,
    "maiz_forraje": 1,
}


def is_seasonal(crop: Crop) -> bool:
    return crop.get("tipo_ciclo") == "anual"


def candidates(start: Crop, catalog: list[Crop]) -> list[Crop]:
    """Next crops: seasonal and from a different botanical family than the start."""
    return [
        c
        for c in catalog
        if is_seasonal(c) and c["id"] != start["id"] and c.get("tipo") != start.get("tipo")
    ]


def water_score(nxt: Crop) -> int:
    if nxt.get("drought_tolerant") == "alto":
        return 3
    return WATER_BY_DEMAND.get(nxt.get("agua", {}).get("demanda", "media"), 2)


def soil_score(start: Crop, nxt: Crop) -> int:
    if nxt.get("tipo") == start.get("tipo"):
        return 1
    score = 1 + (1 if nxt.get("fix_n") else 0) + (1 if nxt.get("breaks_pest_cycle") else 0)
    if nxt.get("erosion_sens") == "alta":
        score -= 1
    return max(1, min(3, score))


def score(start: Crop, nxt: Crop) -> dict[str, int]:
    return {
        "agua": water_score(nxt),
        "tierra": soil_score(start, nxt),
        "forraje": FORAGE_BY_VALUE.get(nxt.get("forage_value", "bajo"), 1),
        "vender": SELLS_WELL.get(nxt["id"], 1),
    }


def fallow_scores() -> dict[str, int]:
    """Not rotating: no extra water, but nothing returned to soil, animals or market."""
    return {"agua": 3, "tierra": 1, "forraje": 1, "vender": 1}


def labels(start: Crop, nxt: Crop) -> list[list[str]]:
    found: list[list[str]] = []
    if nxt.get("fix_n"):
        found.append(["abona_tierra", "bien"])
    elif nxt.get("breaks_pest_cycle") and nxt.get("tipo") != start.get("tipo"):
        found.append(["corta_plagas", "bien"])
    if nxt.get("forage_value") == "alto":
        found.append(["mucho_forraje", "bien"])
    if SELLS_WELL.get(nxt["id"], 1) == 3:
        found.append(["buen_mercado", "bien"])
    demand = nxt.get("agua", {}).get("demanda")
    if demand in ("alta", "muy alta"):
        found.append(["mas_riego", "mal"])
    elif water_score(nxt) == 3:
        found.append(["poco_riego", "bien"])
    if nxt.get("erosion_sens") == "alta":
        found.append(["riesgo_erosion", "mal"])
    return found[:3]


def why(start: Crop, nxt: Crop) -> str:
    if nxt.get("fix_n"):
        return "fija_nitrogeno"
    if nxt.get("breaks_pest_cycle") and nxt.get("tipo") != start.get("tipo"):
        return "corta_plagas"
    if nxt.get("forage_value") == "alto":
        return "forraje_epoca_seca"
    return "diversifica"


def good(start: Crop, nxt: Crop) -> list[str]:
    items = []
    if nxt.get("fix_n"):
        items.append("tierra_fertil")
    if nxt.get("breaks_pest_cycle") and nxt.get("tipo") != start.get("tipo"):
        items.append("menos_plagas")
    if nxt.get("forage_value") == "alto":
        items.append("forraje_animales")
    if nxt.get("deep_rooting"):
        items.append("suelo_suelto")
    if water_score(nxt) == 3:
        items.append("poco_riego")
    return items[:3]


def risks(nxt: Crop, frost_months: bool, dry_season_risk: bool, reservoir_low: bool) -> list[str]:
    items = []
    if frost_months and nxt.get("helada", {}).get("tolerancia") == "baja":
        items.append("helada_dana_cultivo")
    demand = nxt.get("agua", {}).get("demanda")
    if demand in ("alta", "muy alta") and (dry_season_risk or reservoir_low):
        items.append("riego_epoca_seca")
    if nxt.get("erosion_sens") == "alta":
        items.append("riesgo_erosion")
    return items


def confidence(start: Crop, nxt: Crop) -> str:
    documented = nxt.get("fix_n") or (
        nxt.get("breaks_pest_cycle") and nxt.get("tipo") != start.get("tipo")
    )
    return "media" if documented else "baja"


def ranked(start: Crop, catalog: list[Crop], limit: int = 4) -> list[Crop]:
    """Best alternatives first (sum of the four scores), ties by id for a stable table."""
    options = candidates(start, catalog)
    return sorted(options, key=lambda c: (-sum(score(start, c).values()), c["id"]))[:limit]
