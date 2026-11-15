from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class SyncVersion(SQLModel, table=True):
    __tablename__ = "sync_version"

    id: int | None = Field(default=None, primary_key=True)
    creado_en: datetime = Field(default_factory=utcnow)
    hash: str = ""
