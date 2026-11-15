import os
from pathlib import Path

from sqlalchemy import Engine, event
from sqlalchemy.engine import make_url
from sqlmodel import SQLModel, create_engine

DEFAULT_DATABASE_URL = "sqlite:///./data/db/valle.db"


def database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def make_engine(url: str | None = None) -> Engine:
    url = url or database_url()
    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite" and parsed.database not in (None, "", ":memory:"):
        Path(parsed.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def init_db(engine: Engine) -> None:
    import api.models  # noqa: F401  registers every module's tables

    SQLModel.metadata.create_all(engine)
