from datetime import datetime

from sqlmodel import Session, select

from api.modules.reports.models import Report


def add(session: Session, report: Report) -> Report:
    session.add(report)
    session.commit()
    session.refresh(report)
    return report


def find_by_key(session: Session, key: str) -> Report | None:
    return session.exec(select(Report).where(Report.idempotency_key == key)).first()


def recent(session: Session, zone_id: str, tipo: str, since: datetime) -> list[Report]:
    return list(
        session.exec(
            select(Report).where(
                Report.zone_id == zone_id, Report.tipo == tipo, Report.ocurrido_en >= since
            )
        )
    )
