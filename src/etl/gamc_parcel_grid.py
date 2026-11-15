"""Per-plot facts from the GAMC zone maps (distance to channels, periurbano class).

The phone cannot read pixels cheaply, and the GAMC has no plot layer, so each
zone image (`gamc_zone_maps.py`) is reduced here to a coarse grid of about
100 m cells with two values per cell:

- `drenaje`: distance in metres from the cell to the nearest drainage pixel,
  in steps of `STEP_M`, capped at `CAP_M`.
- `periurbano`: 0 none, 1 consolidado, 2 en crecimiento (GAMC Periurbanos).

The layer colours are fixed by the GAMC styles (legends in data/gamc/04/leyendas):
drainage is opaque blue; periurbanos are salmon (consolidated) and green (growing).

Output: data/gamc/04/zonas/grid.json, bundled in the app. Re-runnable.

Usage:
    uv run python -m src.etl.gamc_parcel_grid
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ZONES = ROOT / "data" / "gamc" / "04" / "zonas"
CELL_PX = 12  # about 100 m at 8 m per pixel
STEP_M = 20
CAP_M = 600
M_PER_DEG_LAT = 110_574
M_PER_DEG_LON = 111_320
URBAN = ["", "consolidado", "crecimiento"]


def classify(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    r, g, b, a = (arr[..., i].astype(int) for i in range(4))
    drain = (a > 200) & (b > 200) & (r < 90) & (g > 100) & (g < 170)
    salmon = (a > 120) & (r > 200) & (g < 150) & (b < 130)
    green = (a > 120) & (g > 200) & (r < 160) & (b < 110)
    urban = np.where(salmon, 1, np.where(green, 2, 0))
    return drain, urban


def channel_distance(drain: np.ndarray, cell_px: int, px_m: tuple[float, float]) -> np.ndarray:
    """Metres from each cell centre to the nearest drainage pixel (CAP_M if none)."""
    rows, cols = drain.shape[0] // cell_px, drain.shape[1] // cell_px
    ys, xs = np.nonzero(drain)
    out = np.full((rows, cols), CAP_M, dtype=int)
    if len(ys) == 0:
        return out
    pts = np.stack([xs * px_m[0], ys * px_m[1]], axis=1)
    for r in range(rows):
        cy = (r + 0.5) * cell_px * px_m[1]
        near = pts[np.abs(pts[:, 1] - cy) <= CAP_M]
        if len(near) == 0:
            continue
        for c in range(cols):
            cx = (c + 0.5) * cell_px * px_m[0]
            d = np.hypot(near[:, 0] - cx, near[:, 1] - cy).min()
            out[r, c] = min(CAP_M, int(d))
    return out


def _encode(values: np.ndarray, step: int = 1) -> str:
    return "".join(np.base_repr(int(v) // step, 36).lower() for v in values.ravel())


def zone_grid(img: Image.Image, bbox: list[float], cell_px: int = CELL_PX) -> dict[str, Any]:
    arr = np.array(img.convert("RGBA"))
    drain, urban = classify(arr)
    west, south, east, north = bbox
    height, width = arr.shape[:2]
    mid_lat = (south + north) / 2
    px_m = (
        (east - west) * M_PER_DEG_LON * math.cos(math.radians(mid_lat)) / width,
        (north - south) * M_PER_DEG_LAT / height,
    )
    rows, cols = height // cell_px, width // cell_px
    metres = np.minimum(channel_distance(drain, cell_px, px_m) // STEP_M * STEP_M, CAP_M)
    classes = np.zeros((rows, cols), dtype=int)
    for r in range(rows):
        for c in range(cols):
            block = urban[r * cell_px : (r + 1) * cell_px, c * cell_px : (c + 1) * cell_px]
            counts = np.bincount(block.ravel(), minlength=3)
            classes[r, c] = (
                int(counts[1:].argmax() + 1) if counts[1:].max() > block.size * 0.3 else 0
            )
    return {
        "bbox": bbox,
        "cols": cols,
        "rows": rows,
        "paso_m": STEP_M,
        "tope_m": CAP_M,
        "drenaje": _encode(metres, STEP_M),
        "periurbano": "".join(str(v) for v in classes.ravel()),
    }


def lookup(entry: dict[str, Any], lat: float, lon: float) -> dict[str, Any] | None:
    """Python twin of the app's lookup, used to test the encoding."""
    west, south, east, north = entry["bbox"]
    if not (west <= lon <= east and south <= lat <= north):
        return None
    col = min(entry["cols"] - 1, int((lon - west) / (east - west) * entry["cols"]))
    row = min(entry["rows"] - 1, int((north - lat) / (north - south) * entry["rows"]))
    i = row * entry["cols"] + col
    steps = _decode(entry["drenaje"], entry["cols"] * entry["rows"])
    return {
        "canal_m": steps[i] * entry["paso_m"],
        "periurbano": URBAN[int(entry["periurbano"][i])] or None,
    }


def _decode(text: str, n: int) -> list[int]:
    # Each value is one base-36 digit (CAP_M // STEP_M = 30 < 36).
    assert len(text) == n
    return [int(ch, 36) for ch in text]


def run(zones_dir: Path = ZONES, cell_px: int = CELL_PX) -> dict[str, Any]:
    index = json.loads((zones_dir / "index.json").read_text())
    out: dict[str, Any] = {"zonas": {}}
    for zone_id, meta in sorted(index["zonas"].items()):
        img = Image.open(zones_dir / f"{zone_id}.png")
        out["zonas"][zone_id] = zone_grid(img, meta["bbox"], cell_px)
        print(f"  {zone_id}: {out['zonas'][zone_id]['cols']}x{out['zonas'][zone_id]['rows']}")
    (zones_dir / "grid.json").write_text(json.dumps(out, separators=(",", ":")) + "\n")
    return out


def main() -> None:
    argparse.ArgumentParser().parse_args()
    run()


if __name__ == "__main__":
    main()
