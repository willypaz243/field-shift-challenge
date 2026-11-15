.PHONY: api db-init db-load test

api:
	uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

db-init:
	uv run python -c "from api.core.db import init_db, make_engine; init_db(make_engine())"

db-load:
	uv run python -m src.etl.load_db

test:
	uv run pytest
