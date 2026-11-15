from datetime import datetime, time
from typing import Any

from sqlmodel import Session

from api.modules.water import repository


def _estado(nivel_pct: float | None) -> str | None:
    if nivel_pct is None:
        return None
    if nivel_pct < 20:
        return "critico"
    return "bajo" if nivel_pct < 40 else "normal"


def la_angostura(session: Session) -> dict[str, Any] | None:
    r = repository.get_reservoir(session, "angostura")
    if r is None:
        return None
    updated = datetime.combine(r.actualizado_en, time()).isoformat() if r.actualizado_en else None
    data = {
        "actualizado_en": updated,
        "nivel_pct": r.nivel_pct,
        "volumen_hm3": r.volumen_hm3,
        "estado": _estado(r.nivel_pct),
        "fuente": ["riego_n1"],
    }
    return {k: v for k, v in data.items() if v is not None}
