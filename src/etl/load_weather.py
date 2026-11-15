"""Short-range forecast (14 days) per zone into the `weather` table (task T11, #17).

Source: Open-Meteo forecast API (https://open-meteo.com, free, no key, CC BY 4.0),
which blends national weather models. It is one of the options left open in
API-CONTRACT §12 ("otro servicio meteorológico") and can be swapped for NASA
GEOS-FP or SENAMHI later without touching the API or the app: they only read
the `weather` table.

- One request for all zones (Open-Meteo accepts a list of coordinates).
- Days in America/La_Paz, starting today.
- `granizo` from WMO weather codes 96 and 99 (thunderstorm with hail).
- `confianza` falls with lead time: days 1-3 alta, 4-7 media, 8-14 baja.
- The table is replaced in full (it only holds the current forecast) and a
  `sync_version` row makes phones pull it.

Usage (several times a day, e.g. cron every 6 hours):
    uv run python -m src.etl.load_weather
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from api.core.db import init_db, make_engine  # noqa: E402

URL = "https://api.open-meteo.com/v1/forecast"
DAYS = 14
HAIL_CODES = {96, 99}
SOURCE = "open_meteo"


def confianza(lead: int) -> str:
    if lead < 3:
        return "alta"
    return "media" if lead < 7 else "baja"


def fetch(zones: list[tuple[str, float, float]], get: Callable[..., Any]) -> list[dict[str, Any]]:
    params = {
        "latitude": ",".join(str(lat) for _, lat, _ in zones),
        "longitude": ",".join(str(lon) for _, _, lon in zones),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
        "timezone": "America/La_Paz",
        "forecast_days": DAYS,
    }
    r = get(URL, params=params, timeout=60)
    r.raise_for_status()
    body = r.json()
    return body if isinstance(body, list) else [body]


def rows_for(zone_id: str, daily: dict[str, list[Any]], now: str) -> list[dict[str, Any]]:
    rows = []
    for lead, fecha in enumerate(daily["time"]):
        tmin = daily["temperature_2m_min"][lead]
        tmax = daily["temperature_2m_max"][lead]
        pmm = daily["precipitation_sum"][lead]
        if tmin is None or tmax is None or pmm is None:
            continue
        code = daily["weather_code"][lead]
        rows.append(
            {
                "zone_id": zone_id,
                "fecha": fecha,
                "tmin": tmin,
                "tmax": tmax,
                "pmm": pmm,
                "granizo": 1 if code in HAIL_CODES else 0,
                "confianza": confianza(lead),
                "fuente": SOURCE,
                "actualizado_en": now,
            }
        )
    return rows


def load(engine, get: Callable[..., Any]) -> int:
    init_db(engine)
    now = datetime.now(UTC).isoformat(timespec="seconds")
    raw = engine.raw_connection()
    try:
        con: sqlite3.Connection = raw.driver_connection  # type: ignore[assignment]
        zones = list(con.execute("SELECT id, lat, lon FROM zones ORDER BY id"))
        if not zones:
            return 0
        results = fetch(zones, get)
        rows = [
            r
            for (zone_id, _, _), res in zip(zones, results, strict=True)
            for r in rows_for(zone_id, res["daily"], now)
        ]
        with con:
            con.execute("DELETE FROM weather")
            if rows:
                cols = list(rows[0])
                con.executemany(
                    f"INSERT INTO weather ({', '.join(cols)}) VALUES ({', '.join(':' + c for c in cols)})",
                    rows,
                )
            con.execute("INSERT INTO sync_version (creado_en, hash) VALUES (?, ?)", (now, ""))
    finally:
        raw.close()
    return len(rows)


def main() -> None:
    import requests

    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "data" / "db" / "valle.db"))
    args = ap.parse_args()
    count = load(make_engine(f"sqlite:///{args.db}"), requests.get)
    print(f"weather: {count} rows")


if __name__ == "__main__":
    main()
