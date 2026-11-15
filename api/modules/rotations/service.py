from typing import Any

from sqlmodel import Session

from api.modules.alerts import service as alerts
from api.modules.climate import service as climate
from api.modules.crops import service as crops
from api.modules.rotations import rules

# API-CONTRACT §3.2: a monthly risk starts at 20 % of years.
RISK_SHARE = 0.2
DRY_MONTHS = range(4, 10)
DRY_RAIN_MM = 40


def _span(months: list[int]) -> str:
    names = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    return (
        f"{names[months[0] - 1]}_{names[months[-1] - 1]}"
        if len(months) > 1
        else names[months[0] - 1]
    )


def _climate_facts(session: Session, zone_id: str) -> dict[str, Any]:
    months = climate.climatology(session, zone_id)["meses"]
    frost = sorted(m["mes"] for m in months if m.get("p_helada", 0) >= RISK_SHARE)
    dry = sorted(
        m["mes"]
        for m in months
        if m["mes"] in DRY_MONTHS and m.get("pmm_total", DRY_RAIN_MM) < DRY_RAIN_MM
    )
    return {"frost": frost, "dry": dry}


def catalog(session: Session, zone_id: str) -> dict[str, Any]:
    data = crops.catalog()
    everything = data["crops"]
    facts = _climate_facts(session, zone_id)
    reservoir_low = any(a["tipo"] == "represa_baja" for a in alerts.active_alerts(session, zone_id))
    rotations = []
    for start in (c for c in everything if rules.is_seasonal(c)):
        rotations.append(
            {
                "id": f"{start['id']}-sin_cultivo",
                "secuencia": [start["id"], None],
                "actual_tipica": True,
                "puntaje": rules.fallow_scores(),
                "etiquetas": [["poco_riego", "bien"], ["tierra_se_cansa", "mal"]],
                "por_que": "sin_cambiar",
                "bueno": ["poco_riego", "ya_lo_conoces"],
                "riesgos": ["tierra_se_cansa"],
                "falta_saber": ["rendimiento_parcela"],
                "evidencia": [{"codigo": "practica_actual", "fuente": "catalogo_cultivos"}],
                "confianza": "baja",
            }
        )
        for nxt in rules.ranked(start, everything):
            evidence = [{"codigo": "reglas_catalogo", "fuente": "catalogo_cultivos"}]
            if facts["frost"]:
                evidence.append(
                    {"codigo": f"heladas_{_span(facts['frost'])}", "fuente": "nasa_power"}
                )
            if facts["dry"]:
                evidence.append(
                    {"codigo": f"poca_lluvia_{_span(facts['dry'])}", "fuente": "nasa_imerg"}
                )
            if reservoir_low:
                evidence.append({"codigo": "angostura_baja", "fuente": "riego_n1"})
            rotations.append(
                {
                    "id": f"{start['id']}-{nxt['id']}",
                    "secuencia": [start["id"], nxt["id"]],
                    "puntaje": rules.score(start, nxt),
                    "etiquetas": rules.labels(start, nxt),
                    "por_que": rules.why(start, nxt),
                    "bueno": rules.good(start, nxt),
                    "riesgos": rules.risks(
                        nxt, bool(facts["frost"]), bool(facts["dry"]), reservoir_low
                    ),
                    "falta_saber": [f"precio_{nxt['id']}"],
                    "evidencia": evidence,
                    "confianza": rules.confidence(start, nxt),
                }
            )
    return {"actualizado_en": data.get("actualizado"), "rotaciones": rotations}
