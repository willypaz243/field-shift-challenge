import csv
from pathlib import Path

from sqlmodel import Session, select

from api.core.models import SyncVersion
from api.modules.climate.loader import load_forecasts
from api.modules.climate.models import Forecast

COLUMNS = [
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

ROWS = [
    {
        "fecha": "2026-11-16",
        "tmean": "17.1",
        "tmin": "9.5",
        "tmax": "24.6",
        "pmm": "4.8",
        "et0": "4.2",
        "tmean_baja": "16.0",
        "tmean_alta": "18.2",
        "tmin_baja": "8.9",
        "tmin_alta": "10.2",
        "pmm_baja": "0.0",
        "pmm_alta": "13.0",
        "et0_baja": "3.4",
        "et0_alta": "5.0",
    },
    {
        "fecha": "2026-11-17",
        "tmean": "16.8",
        "tmin": "7.0",
        "tmax": "23.0",
        "pmm": "0.0",
        "et0": "3.9",
        "tmean_baja": "15.7",
        "tmean_alta": "17.9",
        "tmin_baja": "5.8",
        "tmin_alta": "8.2",
        "pmm_baja": "0.0",
        "pmm_alta": "0.0",
        "et0_baja": "3.1",
        "et0_alta": "4.7",
    },
    {
        "fecha": "2027-01-02",
        "tmean": "19.0",
        "tmin": "12.0",
        "tmax": "27.0",
        "pmm": "8.1",
        "et0": "5.1",
        "tmean_baja": "17.9",
        "tmean_alta": "20.1",
        "tmin_baja": "10.4",
        "tmin_alta": "13.6",
        "pmm_baja": "0.0",
        "pmm_alta": "20.0",
        "et0_baja": "4.1",
        "et0_alta": "6.1",
    },
]


def write_csv(path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, COLUMNS)
        writer.writeheader()
        writer.writerows(ROWS)


def test_loader_replaces_rows_and_is_idempotent(engine, tmp_path):
    csv_path = tmp_path / "forecast_valle.csv"
    write_csv(csv_path)
    db = tmp_path / "test.db"

    first = load_forecasts(csv_path, db)
    assert first["zones"] == 1
    assert first["days"] == 3
    assert first["rows"] == 3

    with Session(engine) as session:
        rows = list(session.exec(select(Forecast)))
        assert len(rows) == 3
        assert rows[0].anio == 2026
        assert rows[2].anio == 2027
        assert rows[0].tmean == 17.1
        assert rows[0].tmin_min == 8.9
        assert rows[0].rh is None

    second = load_forecasts(csv_path, db)
    assert second["rows"] == 3
    with Session(engine) as session:
        assert len(list(session.exec(select(Forecast)))) == 3
        assert len(list(session.exec(select(SyncVersion)))) == 2


def test_forecast_endpoint_matches_contract(client, engine, tmp_path):
    write_csv(tmp_path / "forecast_valle.csv")
    load_forecasts(tmp_path / "forecast_valle.csv", tmp_path / "test.db")

    body = client.get("/zones/D9_itocta/forecast").json()

    assert body["zone_id"] == "D9_itocta"
    assert body["anio"] == 2026
    assert body["modelo"]["tipo"] == "fourier_tendencia"
    assert body["modelo"]["backtest"]["mae"]["tmin"] is not None
    assert body["fuente"] == ["nasa_power", "nasa_imerg", "nasa_smap"]
    day = body["dias"][0]
    assert day["fecha"] == "2026-11-16"
    assert day["tmean"] == 17.1
    assert day["et0"] == 4.2
    assert day["incert_min"] == {"tmin": 8.9, "pmm": 0.0}
    assert day["incert_max"] == {"tmin": 10.2, "pmm": 13.0}
    assert "rh" not in day


def test_forecast_unknown_zone_returns_404(client):
    body = client.get("/zones/NOPE/forecast")
    assert body.status_code == 404
    assert body.json()["error"]["codigo"] == "zone_not_found"
