.PHONY: api db-init db-load forecast test web

api:
	uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

db-init:
	uv run python -c "from api.core.db import init_db, make_engine; init_db(make_engine())"

db-load:
	uv run python -m src.etl.load_db

forecast:
	uv run python -m src.model.run_pipeline
	uv run python -m src.etl.load_forecast

test:
	uv run pytest

# Browser preview of the app on http://localhost:8081 (expo-sqlite needs the
# cross-origin isolation headers that scripts/serve-web.mjs sends).
web:
	cd app && EXPO_PUBLIC_API_URL=$${EXPO_PUBLIC_API_URL:-http://localhost:8000} npx expo export --platform web && node scripts/serve-web.mjs
