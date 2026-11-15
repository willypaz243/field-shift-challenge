import os
import sys
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlmodel import SQLModel, create_engine

from api import models  # noqa: F401  (registers tables in SQLModel.metadata)

DEFAULT_DATABASE_URL = "sqlite:///./data/app.db"


def database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def _ensure_sqlite_directory(url: str) -> None:
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite":
        return
    if not parsed.database or parsed.database == ":memory:":
        return
    Path(parsed.database).expanduser().resolve().parent.mkdir(
        parents=True, exist_ok=True
    )


_ensure_sqlite_directory(database_url())
engine = create_engine(
    database_url(),
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    if engine.url.get_backend_name() != "sqlite":
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def reset_db() -> None:
    parsed = make_url(database_url())
    if parsed.get_backend_name() == "sqlite" and parsed.database not in (
        None,
        "",
        ":memory:",
    ):
        path = Path(parsed.database).expanduser()
        for suffix in ("", "-journal", "-wal", "-shm"):
            path.with_name(path.name + suffix).unlink(missing_ok=True)
    else:
        SQLModel.metadata.drop_all(engine)
    init_db()


def database_location() -> str:
    parsed = make_url(database_url())
    if parsed.get_backend_name() == "sqlite":
        return parsed.database or ":memory:"
    return f"{parsed.drivername}://{parsed.host or ''}/{parsed.database or ''}"


def main() -> None:
    if "--reset" in sys.argv[1:]:
        reset_db()
    else:
        init_db()
    print(f"Base de datos lista: {database_location()}")


if __name__ == "__main__":
    main()
