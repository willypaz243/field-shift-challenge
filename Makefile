.PHONY: db-init db-load test

db-init:
	uv run python -c "from api.core.db import init_db, make_engine; init_db(make_engine())"

db-load:
	uv run python -m src.etl.load_db

test:
	uv run pytest
