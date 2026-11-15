from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from api.modules.climate.models import ClimateHistory
from api.modules.rotations import rules
from api.modules.water.models import Reservoir
from api.tests.contract import contract_errors


def crop(**over):
    base = {
        "id": "x",
        "tipo": "cereal",
        "tipo_ciclo": "anual",
        "agua": {"demanda": "media"},
        "helada": {"tolerancia": "media"},
        "fix_n": False,
        "breaks_pest_cycle": False,
        "forage_value": "bajo",
        "erosion_sens": "baja",
        "drought_tolerant": "poco",
        "deep_rooting": False,
    }
    return {**base, **over}


def test_a_legume_scores_best_for_the_soil_after_a_cereal():
    scores = rules.score(
        crop(tipo="cereal"), crop(tipo="leguminosa", fix_n=True, breaks_pest_cycle=True)
    )
    assert scores["tierra"] == 3


def test_same_family_scores_worst_for_the_soil():
    assert rules.score(crop(tipo="cereal"), crop(tipo="cereal"))["tierra"] == 1


def test_water_score_follows_demand_and_drought_tolerance():
    low = rules.score(crop(), crop(agua={"demanda": "media-baja"}))
    high = rules.score(crop(), crop(agua={"demanda": "muy alta"}))
    tolerant = rules.score(crop(), crop(agua={"demanda": "media"}, drought_tolerant="alto"))
    assert (low["agua"], high["agua"], tolerant["agua"]) == (3, 1, 3)


def test_forage_score_follows_forage_value():
    assert [
        rules.score(crop(), crop(forage_value=v))["forraje"] for v in ("alto", "medio", "bajo")
    ] == [3, 2, 1]


def test_not_rotating_saves_water_but_gives_nothing_back():
    assert rules.fallow_scores() == {"agua": 3, "tierra": 1, "forraje": 1, "vender": 1}


def test_labels_are_at_most_three_and_name_the_main_reasons():
    labels = rules.labels(
        crop(tipo="cereal"),
        crop(tipo="leguminosa", fix_n=True, forage_value="alto", agua={"demanda": "alta"}),
    )
    assert len(labels) <= 3
    assert labels[0] == ["abona_tierra", "bien"]


def test_rotations_cover_every_annual_crop_with_three_alternatives(client, engine):
    from api.modules.rotations import service

    with Session(engine) as session:
        body = service.catalog(session, "D9_itocta")

    starts = {r["secuencia"][0] for r in body["rotaciones"]}
    assert {"papa", "choclo", "haba", "trigo"} <= starts
    assert "alfalfa" not in starts
    for start in starts:
        mine = [r for r in body["rotaciones"] if r["secuencia"][0] == start]
        assert sum(1 for r in mine if r["secuencia"][1]) >= 3
        assert sum(1 for r in mine if r.get("actual_tipica")) == 1
    assert contract_errors("Rotations", body) == []


def test_no_rotation_repeats_the_family_of_the_starting_crop(client, engine):
    from api.modules.rotations import service

    with Session(engine) as session:
        body = service.catalog(session, "D9_itocta")
    assert "papa-papaliza" not in {r["id"] for r in body["rotaciones"]}
    assert "choclo-trigo" not in {r["id"] for r in body["rotaciones"]}


def test_climate_and_reservoir_become_evidence_and_risks(client, engine):
    from api.modules.rotations import service

    with Session(engine) as session:
        for year in (2018, 2019):
            for month in (6, 7):
                session.add(
                    ClimateHistory(
                        zone_id="D9_itocta",
                        fecha=datetime(year, month, 10).date(),
                        tmin=-2.0,
                        tmax=20.0,
                        pmm_sat=1.0,
                    )
                )
        session.add(
            Reservoir(
                id="angostura",
                nombre="La Angostura",
                nivel_pct=30.0,
                actualizado_en=(datetime.now(UTC) - timedelta(days=2)).date(),
            )
        )
        session.commit()
        body = service.catalog(session, "D9_itocta")

    papa_haba = next(r for r in body["rotaciones"] if r["id"] == "papa-haba")
    codes = {e["codigo"] for e in papa_haba["evidencia"]}
    assert "angostura_baja" in codes
    assert any(c.startswith("heladas_") for c in codes)


def test_sync_carries_the_rotations(client, engine):
    body = client.get("/sync", params={"zone_id": "D9_itocta"}).json()
    assert len(body["rotaciones"]["rotaciones"]) > 20
