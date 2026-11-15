from sqlalchemy import inspect

from api.core.db import init_db, make_engine

EXPECTED_TABLES = {
    "zones",
    "climate_history",
    "forecasts",
    "crops",
    "events",
    "reservoir",
    "reports",
    "feedback",
    "plans",
    "sync_version",
}


def test_init_db_creates_all_tables(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")

    init_db(engine)

    assert set(inspect(engine).get_table_names()) == EXPECTED_TABLES


TABLE_OWNERS = {
    "zones": "api.modules.zones.models",
    "climate_history": "api.modules.climate.models",
    "forecasts": "api.modules.climate.models",
    "crops": "api.modules.crops.models",
    "events": "api.modules.alerts.models",
    "reservoir": "api.modules.water.models",
    "reports": "api.modules.reports.models",
    "feedback": "api.modules.feedback.models",
    "plans": "api.modules.feedback.models",
    "sync_version": "api.core.models",
}


def test_each_table_is_owned_by_its_module():
    from api import models

    owners = {
        getattr(models, name).__tablename__: getattr(models, name).__module__
        for name in models.__all__
    }

    assert owners == TABLE_OWNERS
    assert not any(module.startswith("api.modules.sync") for module in owners.values())


def test_report_idempotency_key_is_unique(tmp_path):
    from datetime import datetime, timedelta, timezone

    import pytest
    from sqlalchemy.exc import IntegrityError
    from sqlmodel import Session

    from api.modules.reports.models import Report
    from api.modules.zones.models import Zone

    la_paz = timezone(timedelta(hours=-4))
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    init_db(engine)
    with Session(engine) as session:
        session.add(Zone(id="D9_itocta", lat=-17.46, lon=-66.21))
        session.commit()
        session.add(
            Report(
                idempotency_key="key-1",
                tipo="helada",
                zone_id="D9_itocta",
                ocurrido_en=datetime(2026, 11, 15, 6, tzinfo=la_paz),
            )
        )
        session.commit()
        session.add(
            Report(
                idempotency_key="key-1",
                tipo="helada",
                zone_id="D9_itocta",
                ocurrido_en=datetime(2026, 11, 15, 7, tzinfo=la_paz),
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_engine_enables_foreign_keys(tmp_path):
    from sqlalchemy import text

    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")

    with engine.connect() as conn:
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_climate_history_has_one_row_per_zone_and_date(tmp_path):
    import sqlite3

    import pytest

    db = tmp_path / "test.db"
    init_db(make_engine(f"sqlite:///{db}"))
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO zones (id, lat, lon, es_agricola, altitud_alta) VALUES ('D9_itocta', -17.46, -66.21, 1, 0)"
        )
        conn.execute(
            "INSERT INTO climate_history (zone_id, fecha, tmean) VALUES ('D9_itocta', '2026-01-01', 17.0)"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO climate_history (zone_id, fecha, tmean) VALUES ('D9_itocta', '2026-01-01', 18.0)"
            )
