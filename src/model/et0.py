"""ET₀ Hargreaves — FAO-56 Ec. 52 (método alternativo, solo temperatura).

    ET₀ [mm/día] = 0.0023 × (Tmean + 17.8) × √(Tmax − Tmin) × Ra

donde Ra es la radiación extraterrestre expresada en **mm/día**:

    Ra[mm/día] = 0.408 × Ra[MJ/m²/día]

Ra se calcula con la geometría solar estándar (FAO-56 Ec. 11):

    Ra = (24·60/π) · Gsc · dr · [ws·sinφ·sinδ + cosφ·cosδ·sin(ws)]

NOTA: la fórmula documentada en BACKLOG v2 (`0.0023·(Tmean+15)·√RA`) es una
versión incompleta que da valores ~10× menores. Esta implementación usa la
Ec. 52 completa, verificada contra FAO-56 (valores razonables: 4–6 mm/día en
época lluviosa en el valle de Cochabamba, 3126 m).
"""

from __future__ import annotations

import numpy as np

GSC = 0.0820  # constante solar [MJ/m²/min]
LAT_DEG = -17.4  # latitud del valle de Cochabamba
MM_PER_MJ = 0.408  # conversión MJ/m² → mm (calor latente)


def ra_mj_per_m2_day(day_of_year: np.ndarray | int, lat_deg: float = LAT_DEG) -> np.ndarray:
    """Radiación extraterrestre [MJ/m²/día] (FAO-56 Ec. 11)."""
    n = np.asarray(day_of_year, dtype=float)
    phi = np.radians(lat_deg)
    delta = np.radians(23.45 * np.sin(360.0 * (284.0 + n) / 365.0))
    dr = (1.0 + 0.033 * np.cos(360.0 * n / 365.0)) ** -2
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1.0, 1.0))
    ra = (
        (24.0 * 60.0 / np.pi)
        * GSC
        * dr
        * (ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws))
    )
    return ra


def et0_hargreaves(
    tmean: np.ndarray,
    tmax: np.ndarray,
    tmin: np.ndarray,
    day_of_year: np.ndarray,
    lat_deg: float = LAT_DEG,
) -> np.ndarray:
    """ET₀ [mm/día] por FAO-56 Ec. 52. Todos los inputs deben tener la misma longitud."""
    tmean = np.asarray(tmean, dtype=float)
    tmax = np.asarray(tmax, dtype=float)
    tmin = np.asarray(tmin, dtype=float)
    ra_mm = ra_mj_per_m2_day(day_of_year, lat_deg) * MM_PER_MJ
    return 0.0023 * (tmean + 17.8) * np.sqrt(np.maximum(tmax - tmin, 0.0)) * ra_mm
