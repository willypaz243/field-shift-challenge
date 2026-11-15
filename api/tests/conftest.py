import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from api.core.db import get_session, init_db, make_engine
from api.main import create_app
from api.modules.crops.models import Crop
from api.modules.zones.models import Zone


@pytest.fixture
def engine(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    init_db(engine)
    with Session(engine) as session:
        session.add(Zone(id="D9_itocta", nombre="Itocta", lat=-17.4611, lon=-66.2185))
        session.add(Crop(id="haba", nombre="Haba"))
        session.commit()
    return engine


@pytest.fixture
def client(engine):
    app = create_app()

    def session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    return TestClient(app)
